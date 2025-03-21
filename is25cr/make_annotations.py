from openai import OpenAI
import os
import pandas as pd

openai_api_key = '<YOUR-OPENAI-API-KEY>'
text_dir = '<YOUR-TEXT-PATH>/'
out_dir = '<YOUR-ANNOTATIONS-OUTPUT-DIR>/'

with open(openai_api_key, 'r') as file:
    starter_info = file.read().replace('\n','')

client = OpenAI(api_key=starter_info)

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
txtfiles_dir = text_dir
case_filenames = [f for f in os.listdir(txtfiles_dir) if f.endswith(".txt")]

if out_dir == txtfiles_dir:
    exit
os.makedirs(out_dir, exist_ok=True)


print(case_filenames)

if True:
    for idx, case in enumerate(case_filenames):
        print(idx, "/", len(case_filenames))

        # Open file
        with open(txtfiles_dir + case, 'r') as file:
            case_txt = file.read().replace('\n','')

        # Pass query to API
        stream = client.chat.completions.create(
            #    model="gpt-4-turbo",
            # model="o1-preview",
            model="gpt-4-0613",
            messages=[
        #        {"role": "system",
        #               "content": system_prompt},
                {"role": "user",
                    "content": base_prompt + "\n Apply the instructions above to the following query. Query: " + case_txt}
                    ],
        #    temperature=0,
            stream=False,
        )

        # Write to out_dir
        with open(out_dir + os.path.splitext(case)[0]+".bsv", "w") as text_file:
            text_file.write(stream.choices[0].message.content)

        # Re-write as named csv
        # out_names = [f for f in os.listdir(out_dir) if f.endswith(".bsv")]
        # for outname in out_names:
        df = pd.read_csv(out_dir + os.path.splitext(case)[0]+".bsv", sep="|", names = ("event","time"))
        
        df.to_csv(out_dir + os.path.splitext(case)[0]+".csv", index=False)
        

# for chunk in stream:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end="")

