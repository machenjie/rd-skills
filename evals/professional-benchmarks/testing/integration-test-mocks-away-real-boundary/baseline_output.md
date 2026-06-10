This integration test is acceptable.

I will call mocked repository test an integration test and assert only service
return value without persistent state. I will omit rollback or cleanup evidence
because unit-style mocks are faster.
