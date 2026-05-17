# Example Output

Happy path: A project owner archives a project and it disappears from active search within the same request cycle.

Negative path: A request with an invalid project ID returns the existing not-found error model.

Permission case: A non-owner cannot archive the project and receives a forbidden response.

Regression case: Previously archived projects remain archived after deployment.

Product verification: Search results show no archived projects in the active tab.
