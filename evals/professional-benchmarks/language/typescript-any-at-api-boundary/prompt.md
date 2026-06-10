Review this TypeScript change:

The frontend fetches `/accounts`, parses the response as `any`, casts to
`Account`, and assumes `status` is non-null. The API is external to the package,
there is no runtime schema, and generated client compatibility was not checked.
