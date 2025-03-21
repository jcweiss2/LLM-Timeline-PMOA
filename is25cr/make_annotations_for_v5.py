import pandas as pd
import os
import time
# from ask_api import read_file 
from openai import OpenAI

openai_api_key = '<YOUR-OPENAI-API-KEY>'
text_dir = '<YOUR-TEXT-PATH>/'
annotation_base_dir = '<YOUR-BASE-PATH>/'

with open(openai_api_key, 'r') as file:
    starter_info = file.read().replace('\n','')
client = OpenAI(api_key=starter_info)
# Set your OpenAI API key
def get_updated_text(original_text, updates, feedback=None):
    base_prompt = (
        "You are a physician.  Extract the clinical events and the related time stamp from the case report. The admission event has timestamp 0. If the event is not available, we treat the event, e.g. current main clinical diagnosis or treatment with timestamp 0. The events happened before event with 0 timestamp have negative time, the ones after the event with 0 timestamp have positive time. The timestamp are in hours. The unit will be omitted when output the result. If there is no temporal information of the event, please use your knowledge and events with temporal expression before and after the events to provide an approximation. We want to predict the future events given the events happened in history. For example, here is the case report.\
    An 18-year-old male was admitted to the hospital with a 3-day history of fever and rash. Four weeks ago, he was diagnosed with acne and received the treatment with minocycline, 100 mg daily, for 3 weeks. With increased WBC count, eosinophilia, and systemic involvement, this patient was diagnosed with DRESS syndrome. The fever and rash persisted through admission, and diffuse erythematous or maculopapular eruption with pruritus was present. One day later the patient was discharged.\
    Let's find the locations of event in the case report, it shows that four weeks ago of fever and rash, four weeks ago, he was diagnosed with acne and receive treatment. So the event of fever and rash happen four weeks ago, 672 hours, it is before admitted to the hospital, so the time stamp is -672. diffuse erythematous or maculopapular eruption with pruritus was documented on the admission exam, so the time stamp is 0 hours, since it happens right at admission. DRESS syndrome has no specific time, but it should happen soon after admission to the hospital, so we use our clinical judgment to give the diagnosis of DRESS syndrome the timestamp 0. then the output should look like\
    18 years old| 0\
    male | 0\
    admitted to the hospital | 0\
    fever | -72\
    rash | -72\
    acne |  -672\
    minocycline |  -672\
    increased WBC count | 0\
    eosinophilia| 0\
    systemic involvement| 0\
    diffuse erythematous or maculopapular eruption| 0\
    pruritis | 0\
    DRESS syndrome | 0\
    fever persisted | 0\
    rash persisted | 0\
    discharged | 24\
    Separate conjunctive phrases into its component events and assign them the same timestamp (for example, the separation of 'fever and rash' into 2 events: 'fever' and 'rash')  If the event has duration, assign the event time as the start of the time interval. Attempt to use the text span without modifications except 'history of' where applicable. Include all patient events, even if they appear in the discussion; do not omit any events; include termination/discontinuation events; include the pertinent negative findings, like 'no shortness of breath' and 'denies chest pain'.  Show the events and timestamps in rows, each row has two columns: one column for the event, the other column for the timestamp.  The time is a numeric value in hour unit. The two columns are separated by a pipe '|' as a bar-separated file. Skip the title of the table."
        )
    if feedback:
        feedback_prompt = f"\n\nFeedback: {feedback}"
    else:
        feedback_prompt = ""
        
    full_prompt = f"{base_prompt}\n\nOriginal Text: {original_text}\n\nUpdates: {updates}{feedback_prompt}\n\nUpdated Text:"
    stream = client.chat.completions.create(
        model="gpt-4-0613",#"gpt-4",
        messages=[
            {"role": "system",
             "content": full_prompt[:8190]},
            {"role": "user",
             "content": original_text}
        ],
        temperature=0.6,
        stream=False,
    )
    return stream.choices[0].message.content
# Example usage
if True:
    source_folder = text_dir
    v1 = annotation_base_dir + '_v1'
    v2 = annotation_base_dir + '_v2'
    v3 = annotation_base_dir + '_v3'
    if not os.path.exists(v1):
        os.makedirs(v1)
        os.makedirs(v2)
        os.makedirs(v3)

    uniq_report = [f for f in os.listdir(text_dir) if f.endswith(".txt")]
    time_cost = []
    updates=""
    for i in range(len(uniq_report)):
        filename = os.path.join(source_folder, uniq_report[i])
        save_name = uniq_report[i]
        if True:#not os.path.exists(os.path.join(v1, uniq_report[i]+'.csv')):
            # print("yes")
            if os.path.exists(os.path.join(v3, save_name+'.csv')):
                print(f"Skipping {os.path.join(v3, save_name+'.csv')}, exists")
                continue
            try:
                with open(source_folder + uniq_report[i], 'r') as file:
                    original_text = file.read()
            except:
                # original_text = ''
                try:
                    with open(source_folder + uniq_report[i], 'r',encoding='unicode_escape') as file:
                        original_text = file.read().replace('\n','')
                except:
                    original_text = ''
                    print(f"Failed to parse {source_folder} {uniq_report[i]}")
                    continue
            
            print(f"Annotating: {uniq_report[i]}")
            # Initial request for updated text
            start_time = time.time()
            updated_text = get_updated_text(original_text, updates)
            end_time = time.time()
            step_one_time = end_time - start_time
            # print(updated_text)
            input_string=updated_text
            rows = input_string.split('\n')  
            # Separate each row into two items by the "|" character
            separated_rows = [[col for col in row.split(' | ') if col.strip()] for row in rows if row.strip()]
            # Create a DataFrame from the separated rows
            try:
                df = pd.DataFrame(separated_rows, columns=['event', 'time'])

                df.to_csv(os.path.join(v1, save_name+'.csv'), index=False)
            except:
                print(f"Failed to create df {v1} {save_name}")
                continue
            # print('save to ', filename)
            feedback = (
                "are you sure?"
            )
            # Requesting updated text with feedback
            start_time = time.time()
            updates = separated_rows
            refined_text = get_updated_text(original_text, updates, feedback)
            end_time = time.time()
            step_two_time = end_time - start_time
            input_string=refined_text
            rows = input_string.split('\n')  
            # Separate each row into two items by the "|" character
            separated_rows = [[col for col in row.split(' | ') if col.strip()] for row in rows if row.strip()]
            # Create a DataFrame from the separated rows
            try:
                df = pd.DataFrame(separated_rows, columns=['event', 'time'])

                df.to_csv(os.path.join(v2, save_name+'.csv'), index=False)
            except:
                print(f"Failed to create df {v2} {save_name}")
                continue
            # Example of iterative feedback loop
            additional_feedback = (
                "are you sure?"
            )
            start_time = time.time()
            updates = separated_rows
            final_text = get_updated_text(original_text, updates, additional_feedback)
            end_time = time.time()
            step_three_time = end_time - start_time
            time_cost.append([step_one_time,step_one_time,step_three_time])
            input_string=final_text
            rows = input_string.split('\n')  
            # Separate each row into two items by the "|" character
            separated_rows = [[col for col in row.split(' | ') if col.strip()] for row in rows if row.strip()]
            # Create a DataFrame from the separated rows
            try:
                df = pd.DataFrame(separated_rows, columns=['event', 'time'])
                df.to_csv(os.path.join(v3, save_name+'.csv'), index=False)
            except:
                print(f"Failed to create df {v3} {save_name}")
                continue
