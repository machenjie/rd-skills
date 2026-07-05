# Example Output

Flow: User opens project settings, clicks Archive, confirms intent, sees success, and returns to active project list.

States required: loading confirmation, disabled submit during request, success toast, forbidden error, network retry copy, empty active list.

Accessibility: confirmation dialog must trap focus, restore focus to Archive button, and expose destructive action text to assistive technology.
