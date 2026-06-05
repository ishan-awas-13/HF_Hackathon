# **Upgrade Agenda for HF Interview Coach**

## **1. Bulletproof prompts and behaviour:**

**Make it check:**

- Key requirements and skills needed should be present in the entered job description.
- qualifications required/preferred by the recruiter should be present in the job description
- if the entered job desc does not include the abov, the job description is understood as faulty/incomplete then the model returns an error for which a simple python code will make Gradio display "Please enter a complete Jpb Description"

## **2. Fix Tips section:**

**{Trigger as soon as the question generation get triggered}** Make the LLM use the job description as a prompt to generate a set of appropriate tips and suggestions. This will be neatly formatted into a clean look.

## **3. Fix History Section(Plugin will be required):**

- Remove History & Progress Section(Add a Download Option instead)
- Option to download Analysis/ History/ Responses as a pdf report.

This is so user can access their conversation analysis as and when they like.

## **4. Make Response grading/analysis flexible.**

- Implement standards/expectations for response. Use a system where the model reads the job description and therefore creates a set of **keywords** it expects to be in the user's response.
- Without a satisfying percentage of the expected keywords being hit, the scrore shall not be anything above 5/10. Feedback must include advice to make the candidate use important keywords and appropriate terms.

- Expected Keywords in response to better score the response, and STAR format can be excused

## **5. Add support more type of Jobs/Job Descriptions(Not only Tech Based job like now)**

- Make the model be flexible by scanning and understanding the field/industry the job description is of/from.
