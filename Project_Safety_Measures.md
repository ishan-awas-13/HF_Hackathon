\*When you are working with AI agents that are deeply integrated into your IDE, you are essentially building on "shifting sand." Because these agents rely on complex, evolving background services (like the `agentSessions` that failed for you), the most important rule is to **\*\*decouple your project progress from the IDE’s internal memory.\*\*\***

Here is the strategy to keep your project stable and your progress safe:

# **1. Document the "Logic," Not Just the Code**

AI agents are excellent at generating code, but they are terrible at remembering the "why" behind it after a few months.

**Keep an external `project\_roadmap.md`**: When you take a break, document the current state, the next three tasks, and any specific quirks or configurations the agent needed to get things working.

**_Annotate the code:_** If an agent implemented a complex function, add comments explaining the logic. When you return, you won't need the agent to "re-learn" how it did it; you will have a human-readable map.

# 2. Version Control is Your Safety Net

If your IDE becomes unstable, you need to be able to "time travel" back to a state that actually worked.

\* \*\*Commit aggressively:\*\* Even if the code is messy, commit your work to Git daily.

\* \*\*Use Branches:\*\* Don't work on the `main` branch. Create a new branch for every feature or experiment. If the IDE update breaks your environment, you can always revert to the last stable commit in a clean, fresh install of your IDE.

# 3. Decouple Environment from IDE

The most common cause of instability is when your IDE's internal settings become intertwined with your project's dependencies.

\* \*\*Use Virtual Environments:\*\* Always use a `venv` or `conda` environment for your project. This keeps your Python libraries (`pip install...`) separate from the IDE's internal plugins.

\* \*\*Requirements File:\*\* Keep a `requirements.txt` file updated. If your IDE blows up and you have to reinstall it, you can get your project environment back up and running in seconds with `pip install -r requirements.txt`.

# 4. Create "Agent-Agnostic" Checkpoints

AI agents often have "hidden context"—things they know about your project that aren't saved in your files. To prevent losing this:

\* \*\*The "Final Prompt" Rule:\*\* Before you stop for the day (or for a long break), ask the agent: \*"Summarize the current status of this project, the critical dependencies we just set up, and the immediate next steps I should take when I return."\*

\* Save that summary in a text file in your project folder. It serves as an "external brain" that you can feed back into the agent when you return, effectively restoring its context instantly.

# 5. Plan for "Tooling Decay"

AI IDEs change \*fast\*. The version of the "Antigravity" IDE you are using today may not exist (or may look entirely different) by the time you return.

\* \*\*Export configurations:\*\* If you have custom agent settings, prompts, or tool configurations within the IDE, export them as JSON or copy-paste them into a secure document.

\* \*\*Stay Portable:\*\* Keep your code as platform-agnostic as possible. If you are using proprietary "Agent-only" features to do work, see if there is a standard way to achieve that same task (e.g., using a standard terminal command instead of an agent's custom UI button).

By treating your code and your "AI memory" as two separate things that you back up independently, you ensure that if your IDE breaks again, you aren't stuck waiting for a fix—you can just reinstall, point to your folder, and keep going.

When you do get back to this project, do you plan to pick up exactly where you left off, or are you expecting the project requirements to have evolved by then?
