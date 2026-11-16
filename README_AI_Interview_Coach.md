# AI Interview Coach

### AI-Powered Mock Interview Application

AI Interview Coach is a Streamlit-based application that helps
candidates practise job interviews through a structured, ten-question
mock interview. It supports English and Hindi, spoken questions,
microphone or typed answers, optional browser-based video recording,
answer evaluation, and a downloadable report card.

## Features

-   **Four job roles:** Data Analyst, AIML Engineer, Data Scientist, and
    Data Engineer.
-   **Personalised interview setup:** Choose experience level, interview
    scenario, language, skills, target company, job description, and
    focus topics.
-   **Three interview scenarios:**
    -   Standard: a mix of technical and behavioural questions.
    -   Technical: nine technical questions after the introduction.
    -   Behavioral: nine STAR-style behavioural questions after the
        introduction.
-   **Ten questions per interview:** The first question asks for an
    introduction and an explanation of the selected role. The remaining
    nine are based on selected role topics.
-   **English and Hindi interface:** Questions, labels, speech input,
    and feedback follow the selected language.
-   **Voice and text answers:** Record an answer through the microphone
    or type/edit the answer.
-   **Spoken questions and feedback:** Uses text-to-speech where the
    service is available.
-   **Optional video recording:** The browser can show a camera preview
    and record answers after the user gives camera consent and grants
    browser permission.
-   **Answer evaluation:** Compares an answer with an ideal answer and
    rubric; shows match percentage, score out of 10, covered and missed
    points, strengths, areas to improve, and a tip.
-   **Final report card:** Displays the overall score out of 100,
    performance band, average match, recommendations, and question-wise
    feedback.
-   **Downloads:** Export the report as a text file and scores as a CSV
    file; recorded answers can also be downloaded.

## Technology Stack

  -----------------------------------------------------------------------
  Technology                          Purpose
  ----------------------------------- -----------------------------------
  Python                              Main application logic

  Streamlit                           Web interface and session state

  Anthropic Claude API                Question generation and
                                      meaning-based answer evaluation

  Pandas                              Results, report tables, and CSV
                                      export

  SpeechRecognition                   Speech-to-text using Google Web
                                      Speech

  gTTS                                Spoken questions and feedback

  HTML and JavaScript                 Custom browser video recorder
                                      component

  MediaRecorder and getUserMedia      Camera preview and browser-side
                                      video capture
  -----------------------------------------------------------------------

## How the Application Works

1.  **Configure the interview:** Select a role, experience level,
    scenario, language, focus areas, and evaluation rubric. Provide the
    required microphone consent; camera consent is optional.
2.  **Generate questions:** The app creates ten questions with Claude
    when an API key is configured. Without a key, it uses built-in
    role-based question templates.
3.  **Ask each question:** The application presents and speaks one
    question at a time.
4.  **Capture the answer:** Speak using the microphone or type an
    answer. The speech transcript can be edited before evaluation.
5.  **Record video (optional):** If camera consent is provided and
    browser permission is granted, the browser recorder captures the
    answer.
6.  **Evaluate the answer:** The app compares the response with the
    ideal answer and evaluation rubric, then displays a score and
    feedback.
7.  **View the report:** After all ten questions, review the final
    report and download the available results.

## Project Structure

Keep the main application and dependency file in the same project
folder:

``` text
AI-Interview-Coach/
├── app.py
├── requirements.txt
└── README.md
```

If your Python file is currently named `app3.py`, either rename it to
`app.py` or change the run command below to use `app3.py`.

## Requirements

-   Python 3.10 or newer
-   A modern web browser such as Google Chrome or Microsoft Edge
-   Internet connection for Claude API, Google speech recognition, and
    gTTS services
-   Microphone permission for voice answers
-   Camera permission only if you want to use video recording
-   An Anthropic API key for Claude-powered question generation and
    semantic evaluation (optional; offline template and keyword-based
    fallback is available)

## Installation and Setup

### 1. Clone or download the project

Open the project folder in VS Code.

### 2. Create a virtual environment

**Windows PowerShell:**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

``` bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the Anthropic API key (optional)

The app reads `ANTHROPIC_API_KEY` from an environment variable or
Streamlit secrets.

**Windows PowerShell (current terminal session):**

``` powershell
$env:ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Alternatively, create `.streamlit/secrets.toml` in the project folder:

``` toml
ANTHROPIC_API_KEY = "your_anthropic_api_key"
```

Do not publish your API key, commit it to Git, or include it in
screenshots. If no key is configured, the application uses built-in
questions and keyword-based answer checking. This fallback is not
semantic AI evaluation.

The model can be changed with the `ANTHROPIC_MODEL` environment
variable. The default model configured in the application is
`claude-sonnet-5-5`. Confirm that the model identifier is available to
your Anthropic account before running the app.

### 5. Run the application

If the file is named `app.py`:

``` bash
streamlit run app.py
```

If the file is still named `app3.py`:

``` bash
streamlit run app3.py
```

Streamlit will display a local URL in the terminal. Open that URL in
your browser.

## Using the Application

1.  Select English or Hindi.
2.  Choose one of the four job roles and an experience level.
3.  Select Standard, Technical, or Behavioral interview mode.
4.  Add relevant skills, company details, job description, or focus
    topics if needed.
5.  Check that the evaluation rubric totals exactly 10 marks per
    question.
6.  Give microphone consent to start the voice interview. Camera consent
    is optional.
7.  Generate the interview and answer each of the ten questions.
8.  Review the feedback after each answer and continue to the next
    question.
9.  Open the report card at the end and download the report or CSV
    scores.

## Important Notes and Limitations

-   **API fallback:** If the Claude API key is missing or an API request
    fails, the application falls back to built-in questions and
    keyword-based evaluation. Keyword matching is less capable than
    meaning-based evaluation and may not recognise equivalent wording.
-   **Speech recognition:** Microphone transcription uses Google's web
    speech service and requires an internet connection. If transcription
    fails, the user can type or edit the answer.
-   **Text-to-speech:** gTTS requires internet access. Spoken output may
    be unavailable if the service or connection fails.
-   **Browser permissions:** Camera and microphone access depend on
    browser permission. Camera access generally requires localhost or a
    secure HTTPS origin.
-   **Video privacy:** Video capture is optional and starts only after
    the user consents and grants browser permission. The app handles the
    recording in the browser/session; it is not designed as permanent
    cloud video storage.
-   **Evaluation:** AI-generated scores are practice feedback, not a
    certified hiring decision. They should be reviewed critically and
    have not been established as equivalent to a human interviewer's
    judgement.
-   **Rubric configuration:** The rubric total is validated, but the
    current report does not provide a complete per-criterion score
    breakdown.

## Future Enhancements

-   Add more job roles and interview languages.
-   Allow users to write or edit questions and generate questions from
    uploaded job descriptions.
-   Show marks for each rubric criterion and support fully user-defined
    criteria.
-   Add clearer API error messages, retry controls, and human validation
    of AI scores.
-   Add consent-based analysis of speaking pace, eye contact, and filler
    words.
-   Add user accounts and saved interview history.
-   Improve cloud deployment, rate limiting, and mobile accessibility.

## Security and Privacy

-   Keep API credentials in environment variables or Streamlit secrets.
-   Never commit `.streamlit/secrets.toml` or other files containing
    credentials.
-   Ask for microphone and camera permission only when the user chooses
    those features.
-   Do not upload or publish interview recordings or personal answers
    without the candidate's explicit permission.

## Author

**Rahul Raj**\
AI/ML Intern --- Apana Time Tech Solutions

------------------------------------------------------------------------

*AI Interview Coach is an interview-practice prototype intended for
learning and preparation.*
