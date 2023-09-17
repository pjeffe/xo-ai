from asyncio import (set_event_loop, new_event_loop, run)
import os
import guidance
import streamlit as st
import json
import test_data
import traceback

rubric_prompt = """
{{#system~}}
You are an expert in writing rubrics for grading essays written by elementary school students.
{{~/system}}

{{#user~}}
Create a rubric for grading an essay written by a {{grade}}-grade student.
The rubric should be based on these standards: {{standard}}.
The rubric should be specific to the standards for the {{grade}} grade.

The only output you produce should be a JSON array of objects, each of which has the following fields:
 - "section": A short title for the section of the criteria.
 - "criteria": An array of objects that define the different levels of achievement for this section.
   Each object has the following fields:
   - "description": A short textual description of the grading criteria.
   - "score": A point value that is awarded if the criteria is met, in the set of [0,1,2,3] to correspond
   to the achievement levels of [Beginning, Developing, Proficient, Advanced].

Take this as a step-by-step process to make sure that you have covered all the relevant sections of the
standards, and that within each section there is a set of criteria that cover the four given levels of
achievement for that section.

Ensure that the rubric at least contains sections that cover addressing the topic, organization, grammar,
vocabulary, and use of supporting evidence.

Your output should consist only of the JSON array, with no extraneous text and no quotes enclosing it.

This is an example for two sections of the rubric:
[
  {
    "section": "Development with Support/Evidence",
    "criteria": [
      {
        "description": "Does not support opinion with facts, details, and/or reasons. Provides no or inaccurate explanation/analysis of how evidence supports opinion.",
        "score": 0
      },
      {
        "description": "Supports opinion with minimal and/or irrelevant facts, details, and/or reasons. Provides some explanation/analysis of how evidence supports opinion.",
        "score": 1
      },
      {
        "description": "Supports opinion with relevant facts, details, and/or reasons. Provides clear explanation/analysis of how evidence supports opinion.",
        "score": 2
      },
      {
        "description": "Supports opinion skillfully with substantial and relevant facts, details, and/or reasons. Provides insightful explanation/analysis of how evidence supports opinion.",
        "score": 3
      }
    ]
  },
  {
    "section": "Language/Conventions",
    "criteria": [
      {
        "description": "Uses few to no correct sentence structures. Demonstrates limited understanding of grade-level appropriate conventions, and errors interfere with meaning and readability. Uses no academic or domain-specific vocabulary.",
        "score": 0
      },
      {
        "description": "Uses some repetitive yet correct sentence structures. Demonstrates some grade-level appropriate conventions, but errors obscure meaning and readability. Uses limited academic and/or domainspecific vocabulary for audience and purpose",
        "score": 1
      },
      {
        "description": "Uses correct and varied sentence structures. Demonstrates grade-level appropriate conventions; errors are minor and do not obscure meaning and readability. Uses academic and domain- specific vocabulary appropriate for audience and purpose.",
        "score": 2
      },
      {
        "description": "Uses purposeful and varied sentence structures. Demonstrates creativity and flexibility when using conventions (i.e., grammar, punctuation, capitalization, spelling) to enhance meaning and readability. Uses precise and sophisticated academic and domain-specific vocabulary appropriate for audience and purpose.",
        "score": 3
      }
    ]
  }
]
{{~/user}}

{{#assistant~}}
{{gen 'rubric' temperature=0 max_tokens=5000}}
{{~/assistant}}
"""

question_prompt = """
{{#system~}}
You are an expert in writing essay prompts for elementary school students.
You should always use age-appropriate language and be sure not to include any inappropriate details or feedback.
{{~/system}}

{{#user~}}
Create a free-response essay prompt for a {{grade}}-grade student on the topic of {{topic}}.
Make sure that it uses age-appropriate language and subject matter.

The student's resulting essay must be able to be graded against this rubric, which is formatted as a JSON array,
with several sections that each have a set of Criteria, which when satisfied are given the corresponding Score:
```
{{rubric}}
```

Your prompt output consists of three distinct sections: the Introduction, Context, and Question.
Each section is marked by a heading with its section name, separated from the previous section by
a blank line.

The Introduction consists of the following text:
```
You are to write an essay on the subject of <topic>>. The following section contains important information
that you are to use in your essay, and following that is the question that you are to address in your essay:
```

The Context consists of several paragraphs of information that includes facts and other content.
It should be sufficient for the student to be able to construct an excellent essay, based on the Context content alone.
The Context shouldn't be an essay in itself. In particular it shouldn't have a point of view or argue a
particular point. Instead, it should be a collection of important facts, clearly presented, that will
enable the student to create an essay that will get them high scores on the rubric.

The Question must satisfy the following criteria:
- It has clear instructions that guide the student to create an essay that is appropriate for
their grade.
- It asks the student to use the facts in the Context section to build their essay.
- It doesn't just ask the student to repeat the facts in the Context, it asks them to explore themes
that are raised in the Context, and give their own view of them.

Take a step-by-step approach to generating the Context and the Question, to make sure that they satisfy all of the
above criteria. Apply the criteria to what you have generated, and if it doesn't satisfy all of the criteria then
discard it and try again.

The output should be formatted as markdown.

Here is an example of a prompt. Do not use this example, but rather create one of your own that is about
the provided topic and follows this structure:
```
#### Introduction
You are to write an essay on the subject of golf. The following section contains important information that you are to use in your essay, and following that is the question that you are to address in your essay:

#### Context
Golf is a popular sport played by people all around the world. It is a game that requires skill, patience, and strategy. Golf courses are usually large and have many holes for players to try and get their ball into. Players use different clubs to hit the ball and try to get it into the hole with as few strokes as possible. Golf is a fun and challenging game that can be enjoyed by people of all ages.

Golf is believed to have originated in Scotland in the 15th century. It was originally played with a wooden ball and a stick. Over time, the game evolved and became more popular. Today, golf is played on well-maintained courses with grassy fairways and smooth greens. Professional golfers compete in tournaments all over the world, and many people enjoy playing golf as a recreational activity.

Golf is a unique sport because it requires both physical and mental skills. Players need to have good hand-eye coordination and be able to hit the ball accurately. They also need to think strategically and make decisions about which club to use and how much force to use when hitting the ball. Golf is a game that requires concentration and focus, as players need to carefully plan their shots and adjust their technique based on the conditions of the course.

Golf is a sport that can be played by people of all ages and abilities. It is a great way to spend time outdoors and get some exercise. Golf courses are often located in beautiful settings, surrounded by trees and nature. Playing golf can be a peaceful and relaxing experience, as players can enjoy the scenery and the fresh air while they play.

Overall, golf is an exciting and challenging game that can be enjoyed by people of all ages. Whether you are a beginner or an experienced player, golf offers a fun and rewarding experience. So grab your clubs and head out to the golf course for a day of fun and adventure!

#### Question
Think about the skills and qualities that are important in the game of golf, such as patience, strategy, and concentration. Write an essay explaining how these skills and qualities can be helpful in other areas of your life. Use evidence from the context to support your essay. Remember to include an introduction, body paragraphs with supporting details, and a conclusion. Use clear language and proper grammar, punctuation, and capitalization.
```
{{~/user}}

{{#assistant~}}
{{gen 'question' temperature=0 max_tokens=5000}}
{{~/assistant}}
"""

validity_prompt = """
{{#system~}}
You are an expert in grading essays for elementary school students.
You should always use age-appropriate language and be sure not to include any inappropriate details or feedback.
{{~/system}}

{{#user~}}
You are grading an essay from a {{grade}}-grade student that was submitted in response to the prompt.
In all your output, use the second-person singular to address your feedback directly to the student.

Your only task at this stage is to verify whether the content of the essay is directly responsive to the prompt,
and that its subject matches the given topic: "{{topic}}".

The essay should be directly responsive to the prompt, use information contained in the prompt's context,
and conform to its guidance.

Format your output as a JSON object, with a "valid" boolean field that indicates whether the above criteria
is satisfied by the essay, and a "feedback" string field that contains a single paragraph of no more than 6 sentences
that describes exactly how the essay is or isn't valid, and suggests how it could be made to be if it isn't.

Example output:
```
{
  "valid": false,
  "feedback": "Your essay does not address the topic. You talked about a football player instead of discussing the skills and qualities important in the game of football. To make your essay valid, focus on teamwork, strategy, and focus in the context of football and how these skills can be helpful in other areas of your life."
}
```

This is the essay:
```
{{essay}}
```

The essay was submitted in response to this prompt:
```
{{question}}
```
{{~/user}}

{{#assistant~}}
{{gen 'result' temperature=0 max_tokens=2000}}
{{~/assistant}}
"""

grading_prompt = """
{{#system~}}
You are a highly qualified candidate applying for an elementary-school teaching position at a school
with very high standards.
You need to prove to the school that you have excellent skills, especially when it comes to scoring
writing assignments.
You should always use age-appropriate language and be sure not to include any inappropriate details or feedback.
{{~/system}}

{{#user~}}
You are given an assessment that asks you to score an essay from a {{grade}}-grade student.
You need to use this assessment to prove that you are an excellent scorer of essays.

Use the rubric given below to score the essay. The rubric  is formatted as a JSON array,
with several sections that each have a set of Criteria, which when satisfied are given the corresponding Score
for that section.
The essay is to be given a Score for each section of the rubric, based on the highest of the section's
Criteria that it has satisfied.

Work on the grading step-by-step to be sure that each section of the rubric has been scored accurately.
For each of the sections in the rubric, choose the Score for the one row whose Criteria most closely
applies to the essay. Make sure that you are correctly applying the Criteria
and getting the right Score. For every scoring decision, ask yourself whether a higher or lower score
in that section would make more sense.

Be strict in your grading, requiring that the rubric's Criteria really is met in order to assign its Score.

In all your output, use the second-person singular to address your feedback directly to the student.

The only output you produce should be a JSON object with the following fields:
 - "table": A markdown table, with no heading. For each section in the rubric, the table has a row
that contains:
   - A "Criteria" column with the name of the section of the rubric.
   - A "Score" column with the score that you assigned for that section.
   - A "Comments" column that summarizes the reasons why you gave the student the given Score for that Criteria, and
     if the score is less than 3, tells the student what they could do to improve it.
  Only include one Score row for each section of the rubric.

 - "total": The student's total Score points.

 - "summary": A short summary of the grading, of no more than 4 sentences, that highlights the key strengths
   and weaknesses of the student's essay.

 - "comparison": If the following text, which is the content of the student's previous essay,
  is more than 10 words long:
```
{{previous_essay}}
```
  then this field is a summary comparison of the student's current essay with their previous essay, otherwise
  it is an empty string.

This is the rubric:
```
{{rubric}}
```

This is the essay:
```
{{essay}}
```

The essay was submitted in response to this prompt:
```
{{question}}
```

Don't include the actual text of the rubric in the grading output.
{{~/user}}

{{#assistant~}}
{{gen 'grade' temperature=0 max_tokens=5000}}
{{~/assistant}}
"""

grading_qa_prompt = """
{{#system~}}
You are an experienced educator who is an expert at evaluating the grading of other educators.
{{~/system}}

{{#user~}}
You are to evaluate the quality of the following grading that was produced by a {{grade}}-grade teacher:
```
{{score}}
```
The grading is formatted as a JSON object with the following fields:
 - "table": A markdown table that has a row for each section of the grading rubric that was used. Each row contains:
   - A "Criteria" column with the name of the section of the rubric.
   - A "Score" column with the score that the teacher assigned for that section.
   - A "Comments" column that summarizes the reasons why they gave the student the given Score for that Criteria, and
     if the score is less than 3, tells the student what they could do to improve it.

 - "total": The student's total Score points, out of a maximum of {{max_score}}.

 - "summary": A short summary of the grading that highlights the key strengths and weaknesses of the student's essay.

 - "comparison": An optional summary comparison of the student's current essay with their previous essay.

You should evaluate whether there are any apparent problems with the grading, including but not limited to:
 - The comments in the scoring table being in conflict with, or not related to, the criteria.
 - The summary being in conflict with, or not related to, the comments in the scoring table.
 - The comparison, if it exists, being in conflict with, or not related to, the summary.

Format your output as a JSON object, with a "valid" boolean field that is true if no problems were found
with the grading. If there were problems found then include a "feedback" string field that contains a
summary of them in plain text.

Example output:
{
  "valid": false,
  "feedback": "The summary included feedback that was in conflict with the comments in the table."
}

Do not include any content in your output other than the JSON object.
{{~/user}}

{{#assistant~}}
{{gen 'result' temperature=0 max_tokens=5000}}
{{~/assistant}}
"""

test_prompt = """
{{#system~}}
You are student simulator that can simulate the writing output of students with different levels of skill.
{{~/system}}

{{#user~}}
You are to write an essay that would be produced by a {{grade}}-grade student, with a skill level of "{{quality}}".
The essay is supposed to be in response to this prompt question, but for "low" and "medium" skill levels
it shouldn't be fully responsive to it:
```
{{question}}
```
A "low" skill essay should use simple sentence structures and limited vocabulary, have straightforward ideas,
and use very poor grammar. It should only have one paragraph, and shouldn't include an introduction or conclusion. It should
be on the topic of the prompt question, but it shouldn't include evidence from the context to support its statements.

A "medium" skill essay should use simple sentence structures and limited vocabulary, and have several grammatical
errors. It should have no more than 2 paragraphs, and it should lack some of the attributes asked for in the prompt
question; for example, only include one piece of evidence from the context to support its statements.

A "high" skill essay should use complex sentence structures and an extensive vocabulary. It should be written
at a skill level that is 2-3 grades higher than {{grade}} grade. It should address all the themes and facts
presented in the context of the prompt question.

Approach this in a step-by-step way to make sure that the essay you produce represents the given
skill level for the given grade.

Your output should only be the content of the essay, in simple text, with no title or headings,
and no mention of the skill level or the expected grading.
{{~/user}}

{{#assistant~}}
{{gen 'essay' temperature=0 max_tokens=2000}}
{{~/assistant}}
"""

class Agent:
    def __init__(self, api_key):
        self.standard = 'Common Core State Standards for English Language Arts & Literacy: CCSS.ELA-LITERACY.W.4.9'
        self.max_tries = 5

        self.grade = None
        self.rubric = None
        self.max_score = None
        self.topic = None
        self.question = None

        # init the Guidance templates
        guidance.llm = guidance.llms.OpenAI("gpt-4", api_key=api_key, max_retries=20)

        self.rubric_template = guidance(rubric_prompt)
        self.question_template = guidance(question_prompt)
        self.validity_template = guidance(validity_prompt)
        self.grading_template = guidance(grading_prompt)
        self.grading_qa_template = guidance(grading_qa_prompt)
        self.test_template = guidance(test_prompt)

    def generate_rubric(self, grade):
        self.grade = grade
        self.rubric = None
        tries = 0
        while not self.rubric and tries < self.max_tries:
            try:
                rubric_str = self.rubric_template(standard=self.standard, grade=grade)['rubric']
                # print(f'\nrubric = {rubric_str}')
                self.rubric = json.loads(rubric_str)

                # sanity-check rubric
                self.max_score = len(self.rubric) * 3
                if self.max_score == 0:
                    raise Exception('rubric contains no sections')
                for section in self.rubric:
                    if len(section['criteria']) != 4:
                        raise Exception(f'section doesn\'t have four criteria: {section}')
                    score = 0
                    for criteria in section['criteria']:
                        if len(criteria['description']) == 0:
                            raise Exception(f'missing description in criteria: {criteria}')
                        score += criteria['score']
                    if score != 6:
                        raise Exception(f'incorrect scores in section: {section}')
            except Exception as exc:
                print(f'error getting rubric: {exc}')
                self.rubric = None
                tries += 1

    def get_display_rubric(self):
        if self.rubric:
            table = '| Criteria | Score |\n| --- | --- |\n'
            for section in self.rubric:
                table += '| **' + section['section'] + '** |\n'
                for criteria in section['criteria']:
                    table += '| ' + criteria['description'] + ' | ' + str(criteria['score']) + ' |\n'
            return table
        else:
            return None

    def get_question(self, topic):
        if not self.topic or self.topic != topic:
            self.topic = topic
            self.question = None
            tries = 0
            while not self.question and tries < self.max_tries:
                try:
                    while not self.question and tries < self.max_tries:
                        question = self.question_template(grade=self.grade, topic=topic, rubric=self.rubric)['question']
                        if question and 'Introduction' in question and 'Context' in question and 'Question' in question:
                            self.question = question
                        else:
                            raise Exception(f'invalid question: {question}')
                except Exception as exc:
                    print(f'error getting question: {exc}')
                    tries += 1
        return self.question

    def check_valid(self, essay):
        validity = None
        tries = 0
        while not validity and tries < self.max_tries:
            try:
                validity_str = self.validity_template(grade=self.grade, essay=essay, topic=self.topic,
                                                      question=self.question)['result']
                validity = json.loads(validity_str)
            except Exception as exc:
                print(f'error checking validity: {exc}')
                tries += 1
        return validity

    def score(self, essay, previous_essay):
        score = None
        tries = 0
        while not score and tries < self.max_tries:
            try:
                score_str = self.grading_template(rubric=self.rubric, grade=self.grade, essay=essay, topic=self.topic,
                                              question=self.question, previous_essay=previous_essay)['grade']
                # check the scoring for consistency and quality
                qa_str = self.grading_qa_template(score=score_str, grade=self.grade, max_score=self.max_score)['result']
                print(f'qa result = {qa_str}')
                if qa_str:
                    qa = json.loads(qa_str)
                    if qa['valid']:
                        score = json.loads(score_str)
                    else:
                        raise Exception(f"got qa error: {qa['feedback']}")
                else:
                    raise Exception('got no output from qa')
            except Exception as exc:
                print(f'error getting score: {exc}')
                score = None
                tries += 1
        return score

    def get_test_data(self, quality):
        data = None
        tries = 0
        while not data and tries < self.max_tries:
            try:
                data = self.test_template(grade=self.grade, quality=quality, question=self.question, rubric=self.rubric)['essay']
            except Exception as exc:
                print(f'error getting test data: {exc}')
                tries += 1
        return data

    def get_max_score(self):
        return self.max_score


async def main():
    canned_tests = {"Low": test_data.baseball_poor, "Medium": test_data.baseball_fair, "High": test_data.baseball_excellent}
    try:
        if 'agent' not in st.session_state:
            api_key = st.secrets['API_KEY']
            st.session_state.agent = Agent(api_key)
        agent: Agent = st.session_state.agent

        st.set_page_config(page_title="AI for Education")

        # generate the rubric for the given grade
        grade = (st.selectbox('Select your grade level:',
                              ('First','Second','Third','Fourth','Fifth','Sixth','Seventh','Eighth',
                               'Ninth','Tenth','Eleventh','Twelfth'), index=3))
        if 'grade' not in st.session_state or grade != st.session_state['grade']:
            # print(f'generating rubric for the {grade} grade')
            st.session_state['grade'] = grade
            agent.generate_rubric(grade)

        rubric = agent.get_display_rubric()
        if rubric:
            st.markdown(f"""
##### You will be given writing questions on a topic of your choice.
Your responses will be graded according to this rubric:

{rubric}
""")

            if 'previous_essay' not in st.session_state:
                st.session_state['previous_essay'] = ''
            previous_essay = st.session_state['previous_essay']

            st.write("\n\n")
            topic = st.text_input('Enter a topic for your essay')
            if len(topic) > 0:
                # generate a question for the topic
                question = agent.get_question(topic)
                # print(f'\nquestion = {question}')
                # print(f'\ntopic in question = ', topic in question)

                # simple test for inappropriate or otherwise problematic topics
                if topic not in question:
                    st.markdown("##### I'm sorry but I can't produce a prompt for that topic. Please choose a different topic.")
                else:
                    st.markdown(question)

                    # three options: auto-generate essay, use canned test essay, or enter your own
                    with st.form('auto_form'):
                        auto_test = st.form_submit_button('Generate Test Essay')
                        auto_quality = st.radio('Quality of test essay:', ('Low', 'Medium', 'High'),
                                                key='auto_qual', horizontal=True)

                    with st.form('canned_form'):
                        canned_test = st.form_submit_button('Use Canned Test Essay')
                        canned_quality = st.radio('Quality of test essay:', ('Low', 'Medium', 'High'),
                                                  key='canned_qual', horizontal=True)

                    with st.form('entered_form'):
                        entered_text = st.text_area('Enter your own essay here:')
                        submit = st.form_submit_button('Submit')

                    if auto_test:
                        st.session_state.essay = agent.get_test_data(auto_quality)
                        st.markdown(f'##### Generated {auto_quality} quality essay:')
                        st.write(st.session_state.essay)

                    elif canned_test:
                        st.session_state.essay = canned_tests[canned_quality]
                        st.markdown(f'##### Canned {canned_quality} quality essay:')
                        st.write(st.session_state.essay)

                    else:
                        st.session_state.essay = entered_text

                    if len(st.session_state.essay) > 0:
                        essay = st.session_state.essay
                        # print(f'\nessay = {essay}')

                        # first check if the essay is a valid response to the prompt
                        validity = agent.check_valid(essay)
                        # print(f'\nvalidity = {validity}')

                        if validity['valid']:
                            score = agent.score(essay, previous_essay)
                            st.markdown(f"#### Your grade: {score['total']} / {agent.get_max_score()}")
                            st.markdown(score['table'])
                            st.write("\n\n")
                            st.markdown(f'##### Summary')
                            st.markdown(score['summary'])
                            if score['comparison']:
                                st.markdown(f'##### Comparison with previous essay')
                                st.markdown(score['comparison'])
                            st.session_state['previous_essay'] = essay
                            # print(f'\nscore = {score}')
                        else:
                            st.markdown(f'##### Feedback')
                            st.markdown(validity['feedback'])
        else:
            st.markdown('#### Error generating rubric, please try again a bit later')

    except Exception:
        st.write('Error occurred, please try again later\n\n')
        st.write(traceback.format_exc())

loop = new_event_loop()
set_event_loop(loop)
run(main())
