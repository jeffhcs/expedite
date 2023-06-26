# Expedite: Autonomous Technical Onboarding Agent

Expedite is an autonomous technical onboarding agent designed to streamline and automate the onboarding process for new hires, saving time and reducing costs for businesses. By leveraging natural language processing and machine learning, Expedite can quickly and accurately set up a new employee's coding environment, ensuring a consistent and error-free experience.

## Key Features

- **Automated onboarding**: Expedite automates the entire onboarding process, reducing the time it takes for new hires to set up their coding environment from weeks to just a day.
- **Adaptive**: Expedite can adapt to different user IDs and devices, handling edge cases that competitors like Chef or Ansible currently cannot.
- **Error documentation**: Expedite documents all errors and successful skills within separate short-term and long-term databases for quick retrieval and implementation.
- **Skill Library**: Expedite stores successful onboarding processes in a Skill Library hosted on Pinecone's vector database for long-term memory, ensuring that future onboarding experiences are even more efficient.
- **User-friendly**: Expedite runs locally and is planned to be on an online portal for ease of use for non-technical employees.

## How It Works

1. **Input**: The user navigates to the Expedite website, pastes their onboarding instructions from their document, and hits the onboard button.
2. **Planning**: Expedite carves out a high-level plan to automatically and rapidly set up the user's environment, breaking it down into individual steps.
3. **Execution**: Each step is given to an inner loop, which further deconstructs it to accomplish the task. Expedite evaluates internal step and general overall history and decides whether to input a shell command to interact with its environment or interact with the user (e.g., asking for passwords, confirmation, etc.).
4. **Self-evaluation**: Expedite executes the action and self-evaluates to determine if the step is complete, recursively continuing if not.
5. **Reflection**: The outer "plan loop" considers the completed steps and processes taken, reflecting on the errors encountered and the steps taken to solve them. These are saved in a skill library for faster resolution in the future.

## Benefits

- **Improved employee satisfaction**: Automating the onboarding process can increase employee retention by over 16% and improve the company's reputation.
- **Reduced costs**: Expedite can reduce the average cost of onboarding a technical employee ($4,100) by cutting the time it takes to set up a fully prepared coding environment from weeks to just a day.
- **Increased revenue**: Automating key parts of the onboarding experience can improve the company's revenue by 60% year-on-year.
- **DevOps team support**: Expedite reduces the burden on the DevOps team, allowing them to focus on high-risk, high-impact infrastructure issues rather than manually documenting redundant and tedious errors that occur during setup for new hires.

## Conclusion

Expedite is a powerful tool that can revolutionize the technical onboarding process for businesses, improving employee satisfaction, reducing costs, and boosting revenue. With Expedite, you can move onward with a fast onboard.
