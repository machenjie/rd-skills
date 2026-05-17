# Cpp Professional Usage Checklist

- Use RAII for every owned resource.
- Remove or block undefined behavior.
- Avoid raw owning pointers unless justified and contained.
- State ABI compatibility policy for public/native boundaries.
- Keep exception or error-code model consistent.
- Document thread safety and memory ordering where relevant.
- Run sanitizer, static analysis, and portability checks for critical code.
- Review build flags, target platforms, and native dependencies.
