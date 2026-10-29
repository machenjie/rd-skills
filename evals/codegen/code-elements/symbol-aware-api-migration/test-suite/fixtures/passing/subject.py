"""Narrow fictional API migration; not a general Python name resolver."""
import ast


def migrate(source):
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ValueError("invalid Python source") from error
    raw = source.encode("utf-8")
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    def start(node):
        return offsets[node.lineno - 1] + node.col_offset
    def end(node):
        return offsets[node.end_lineno - 1] + node.end_col_offset
    bindings, imports, unresolved = {}, [], []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                if local in bindings:
                    unresolved.append("rebound import: " + local)
                bindings[local] = (alias.name, "module")
                if alias.name == "legacy_api":
                    imports.append((node, "import current_api as " + local))
                    if len(node.names) != 1:
                        unresolved.append("combined import requires judgment")
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname or alias.name
                if local in bindings:
                    unresolved.append("rebound import: " + local)
                bindings[local] = (node.module, alias.name)
            if node.module == "legacy_api":
                imports.append((node, "from current_api import " + ", ".join(
                    alias.name + (" as " + alias.asname if alias.asname else "")
                    for alias in node.names)))
                if node.level or any(alias.name != "fetch" for alias in node.names):
                    unresolved.append("unsupported imported symbol")
    old_names = {name for name, binding in bindings.items() if binding[0] == "legacy_api"}
    if old_names:
        scoped = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
                  ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
        if any(isinstance(node, scoped) for node in ast.walk(tree)):
            unresolved.append("scope requires symbol judgment")
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in old_names and isinstance(node.ctx, (ast.Store, ast.Del)):
                unresolved.append("rebound target: " + node.id)
    calls, consumed = [], set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            name = function.value
            binding = bindings.get(name.id)
            matches = binding is not None and binding[1] == "module" and function.attr == "fetch"
        elif isinstance(function, ast.Name):
            name = function
            binding = bindings.get(name.id)
            matches = binding is not None and binding[1] == "fetch"
        else:
            continue
        if not matches or binding[0] != "legacy_api":
            continue
        consumed.add(name)
        if (node.lineno != node.end_lineno or len(node.args) != 1
                or isinstance(node.args[0], ast.Starred)
                or any(keyword.arg not in {"strict", "release"} for keyword in node.keywords)):
            unresolved.append("unsupported call at line " + str(node.lineno))
        calls.append(node)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in old_names and isinstance(node.ctx, ast.Load) and node not in consumed:
            unresolved.append("function value or dynamic use: " + node.id)
    edits = []
    if not unresolved:
        edits.extend((start(node), end(node), text.encode()) for node, text in imports)
        for node in calls:
            explicit = {keyword.arg for keyword in node.keywords}
            defaults = [name + "=True" for name in ("strict", "release") if name not in explicit]
            if defaults:
                position = end(node) - 1
                prefix = " " if raw[start(node):position].rstrip().endswith(b",") else ", "
                edits.append((position, position, (prefix + ", ".join(defaults)).encode()))
        for first, last, replacement in sorted(edits, reverse=True):
            raw = raw[:first] + replacement + raw[last:]
    output = raw.decode("utf-8")
    remaining = ast.parse(output)
    old_lines, new_lines = [], []
    for node in remaining.body:
        modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                   else [node.module] if isinstance(node, ast.ImportFrom) else [])
        if "legacy_api" in modules:
            old_lines.append(node.lineno)
        if "current_api" in modules:
            new_lines.append(node.lineno)
    return {"source": output, "changed_calls": len(calls) if not unresolved else 0,
            "unresolved": sorted(set(unresolved)), "residual_import_lines": old_lines,
            "mixed": bool(old_lines and new_lines)}
