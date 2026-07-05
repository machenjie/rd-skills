# TypeScript Professional Usage Checklist

- Confirm `strict` mode or document approved exception.
- Replace `any` with `unknown`, narrowing, generics, or schemas.
- Validate API, storage, message, and SDK boundaries at runtime.
- Keep frontend DTOs separate from backend internals.
- Handle async errors and cancellation where relevant.
- Review state model and public type compatibility.
- Check bundle impact for frontend changes.
- Run typecheck and behavior tests.
