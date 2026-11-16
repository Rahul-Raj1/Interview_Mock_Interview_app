"""AI Interview Coach - Streamlit app (English + Hindi).
4 roles, 10 questions (Q1 = introduction + role of the field, Q2-Q10 follow the chosen scenario),
spoken by AI -> answer with the mic (+ automatic video recording) -> speech-to-text -> compared with the ideal answer
-> report card. Everything the user sees and hears follows the chosen language (English or Hindi)."""
import base64, hashlib, io, json, os, random, tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
# code: (speech-to-text code, text-to-speech code, language name sent to the AI)
LANGS = {"en": ("en-US", "en", "English"), "hi": ("hi-IN", "hi", "Hindi (Devanagari script)")}
LANG_NAMES = {"en": "English", "hi": "हिन्दी (Hindi)"}

# ---------- translations: key -> (English, Hindi) ----------
T = {
    "title": ("🎙️ AI Interview Coach", "🎙️ AI इंटरव्यू कोच"),
    "sub": ("Practise a 10-question mock interview with a spoken interviewer, voice answers, video recording and an instant report card.",
            "बोलने वाले इंटरव्यूअर, आवाज़ में उत्तर, वीडियो रिकॉर्डिंग और तुरंत रिपोर्ट कार्ड के साथ 10 प्रश्नों के मॉक इंटरव्यू का अभ्यास करें।"),
    "role": ("Job role", "नौकरी की भूमिका"),
    "level": ("Experience level", "अनुभव का स्तर"),
    "scen": ("Interview scenario", "इंटरव्यू का प्रकार"),
    "scen_help": ("Technical: all 9 questions technical. Behavioral: all 9 behavioral. Standard: a mix.",
                  "तकनीकी: सभी 9 प्रश्न तकनीकी। व्यवहारिक: सभी 9 प्रश्न व्यवहारिक। मानक: दोनों का मिश्रण।"),
    "Entry-level": ("Entry-level", "शुरुआती स्तर"), "Mid-level": ("Mid-level", "मध्यम स्तर"), "Senior": ("Senior", "वरिष्ठ"),
    "Standard": ("Standard", "मानक"), "Technical": ("Technical", "तकनीकी"), "Behavioral": ("Behavioral", "व्यवहारिक"),
    "Data Analyst": ("Data Analyst", "डेटा एनालिस्ट"), "AIML Engineer": ("AIML Engineer", "AIML इंजीनियर"),
    "Data Scientist": ("Data Scientist", "डेटा साइंटिस्ट"), "Data Engineer": ("Data Engineer", "डेटा इंजीनियर"),
    "skills": ("Your key skills", "आपके मुख्य कौशल"), "skills_ph": ("SQL, Python, Power BI, statistics…", "SQL, Python, Power BI, सांख्यिकी…"),
    "company": ("Target company ", "लक्षित कंपनी "),
    "jd": ("Job description / role requirements", "जॉब डिस्क्रिप्शन / भूमिका की आवश्यकताएँ"),
    "focus": ("Topics to focus on", "जिन विषयों पर ध्यान देना है"),
    "rub_h": ("**Evaluation rubric (must total 10 marks per question)**", "**मूल्यांकन रूब्रिक (हर प्रश्न के लिए कुल 10 अंक होने चाहिए)**"),
    "Technical accuracy": ("Technical accuracy", "तकनीकी सटीकता"),
    "Explanation and structure": ("Explanation and structure", "व्याख्या और संरचना"),
    "Practical example": ("Practical example", "व्यावहारिक उदाहरण"), "Communication": ("Communication", "संवाद कौशल"),
    "rub_tot": ("Current rubric total: {n}/10", "वर्तमान रूब्रिक कुल: {n}/10"),
    "mic_c": ("I consent to microphone recording for transcription and answer evaluation.",
              "मैं ट्रांसक्रिप्शन और उत्तर के मूल्यांकन के लिए माइक्रोफ़ोन रिकॉर्डिंग की सहमति देता/देती हूँ।"),
    "cam_c": ("I consent to camera access: live preview and automatic video recording of my answers (kept only in this browser session, never uploaded).",
              "मैं कैमरा एक्सेस की सहमति देता/देती हूँ: लाइव प्रीव्यू और मेरे उत्तरों की स्वचालित वीडियो रिकॉर्डिंग (केवल इस ब्राउज़र सत्र में रहती है, अपलोड नहीं होती)।"),
    "gen": ("Generate Mock Interview", "मॉक इंटरव्यू बनाएँ"),
    "err_rub": ("Please make the evaluation rubric total exactly 10 marks.", "कृपया मूल्यांकन रूब्रिक का कुल योग ठीक 10 अंक रखें।"),
    "err_mic": ("Please provide microphone consent before starting the voice interview.",
                "आवाज़ वाला इंटरव्यू शुरू करने से पहले कृपया माइक्रोफ़ोन की सहमति दें।"),
    "spin_gen": ("Generating your interview…", "आपका इंटरव्यू तैयार हो रहा है…"),
    "prog": ("Question {n} of 10 · {role} · {sc}", "प्रश्न {n} / 10 · {role} · {sc}"),
    "cam_prev": ("Camera preview", "कैमरा प्रीव्यू"),
    "mic": ("🎤 Click the mic, speak your answer, then click stop", "🎤 माइक दबाएँ, अपना उत्तर बोलें, फिर स्टॉप दबाएँ"),
    "spin_stt": ("Converting your speech to text…", "आपकी आवाज़ को टेक्स्ट में बदला जा रहा है…"),
    "ans_lbl": ("Your answer (edit the transcript if the mic misheard anything)",
                "आपका उत्तर (अगर माइक ने कुछ गलत सुना हो तो ट्रांसक्रिप्ट सुधारें)"),
    "check": ("Check my answer", "मेरा उत्तर जाँचें"),
    "warn_empty": ("Please record or type an answer first.", "कृपया पहले उत्तर रिकॉर्ड करें या टाइप करें।"),
    "spin_cmp": ("Comparing with the ideal answer…", "आदर्श उत्तर से तुलना की जा रही है…"),
    "fb_note": ("No API key found: questions are randomly assembled from built-in topics and answers are checked by keywords. "
                "Set ANTHROPIC_API_KEY for fully AI-generated random questions and meaning-based checking.",
                "API कुंजी नहीं मिली: प्रश्न अंतर्निहित विषयों से बनाए गए हैं और उत्तर कीवर्ड से जाँचे जाते हैं। "
                "पूरी तरह AI-निर्मित प्रश्नों और अर्थ-आधारित जाँच के लिए ANTHROPIC_API_KEY सेट करें।"),
    "your": ("**🗣️ Your answer**", "**🗣️ आपका उत्तर**"), "ideal": ("**✅ Ideal answer**", "**✅ आदर्श उत्तर**"),
    "m_match": ("Match with ideal answer", "आदर्श उत्तर से मेल"), "m_score": ("Score", "अंक"), "m_verd": ("Verdict", "निर्णय"),
    "cov": ("**Points you covered**", "**जिन बिंदुओं को आपने कवर किया**"), "none_yet": ("None yet", "अभी कोई नहीं"),
    "mis": ("**Points you missed**", "**जिन बिंदुओं को आप चूक गए**"), "nothing": ("Nothing important", "कुछ महत्वपूर्ण नहीं"),
    "stre": ("**Strengths**", "**मजबूत पक्ष**"), "impr": ("**To improve**", "**सुधार के लिए**"),
    "tipl": ("**Tip:** {x}", "**सुझाव:** {x}"),
    "view": ("View report card", "रिपोर्ट कार्ड देखें"), "nextq": ("Next question", "अगला प्रश्न"),
    "v_ok": ("Correct", "सही"), "v_part": ("Partially correct", "आंशिक रूप से सही"), "v_bad": ("Incorrect", "गलत"),
    "le_rel": ("Relevant points mentioned: {x}", "उल्लेख किए गए प्रासंगिक बिंदु: {x}"),
    "le_try": ("You attempted the question.", "आपने प्रश्न का उत्तर देने का प्रयास किया।"),
    "le_nopts": ("Points not detected: {x}", "जो बिंदु नहीं मिले: {x}"),
    "le_nogap": ("No keyword gaps detected.", "कोई कीवर्ड कमी नहीं मिली।"),
    "le_tip": ("Explain the key concept, describe your approach, and add a relevant practical example.",
               "मुख्य अवधारणा समझाएँ, अपना तरीका बताएँ और एक प्रासंगिक व्यावहारिक उदाहरण जोड़ें।"),
    "le_spm": ("Expected terms not detected: {x}. ", "अपेक्षित शब्द नहीं मिले: {x}। "),
    "le_spo": ("Some expected terms were detected. ", "कुछ अपेक्षित शब्द मिले। "),
    "rep_t": ("📋 Report card", "📋 रिपोर्ट कार्ड"), "rep_tot": ("Total score", "कुल अंक"), "rep_avg": ("Average match", "औसत मेल"),
    "b1": ("Excellent: interview-ready", "उत्कृष्ट: इंटरव्यू के लिए तैयार"),
    "b2": ("Good: a few gaps to close", "अच्छा: कुछ कमियाँ दूर करनी हैं"),
    "b3": ("Developing: practise key topics", "विकासशील: मुख्य विषयों का अभ्यास करें"),
    "b4": ("Needs work: start with fundamentals", "मेहनत की ज़रूरत: बुनियादी बातों से शुरू करें"),
    "c_q": ("Q", "प्र."), "c_question": ("Question", "प्रश्न"), "c_match": ("Match %", "मेल %"), "c_score": ("Score", "अंक"),
    "c_verd": ("Verdict", "निर्णय"),
    "rec_h": ("**Recommendations**", "**सिफारिशें**"), "rec_rev": ("- Revisit: {x}", "- दोबारा देखें: {x}"),
    "rec_pr": ("- Practise answering aloud with a clear structure and one concrete example.",
               "- स्पष्ट संरचना और एक ठोस उदाहरण के साथ ज़ोर से उत्तर देने का अभ्यास करें।"),
    "exp": ("Q{n} · {s}/10 · {m}% match · {v}", "प्र.{n} · {s}/10 · {m}% मेल · {v}"),
    "q_l": ("**Question:** {x}", "**प्रश्न:** {x}"),
    "miss_l": ("**Missed:** {x}  \n**Tip:** {tip}", "**छूटा:** {x}  \n**सुझाव:** {tip}"), "nothing2": ("nothing important", "कुछ महत्वपूर्ण नहीं"),
    "dl_txt": ("Download report (.txt)", "रिपोर्ट डाउनलोड करें (.txt)"), "dl_csv": ("Download scores (.csv)", "अंक डाउनलोड करें (.csv)"),
    "new": ("Start a new interview", "नया इंटरव्यू शुरू करें"),
    "r_head": ("AI INTERVIEW COACH REPORT", "AI इंटरव्यू कोच रिपोर्ट"), "r_score": ("Score: {t}/100 ({b})", "अंक: {t}/100 ({b})"),
    "r_q": ("Q{n} ({s}/10, {m}% match, {v}): {q}", "प्र.{n} ({s}/10, {m}% मेल, {v}): {q}"),
    "r_ans": ("Your answer: {x}", "आपका उत्तर: {x}"), "r_ideal": ("Ideal answer: {x}", "आदर्श उत्तर: {x}"),
    "r_mis": ("Missed: {x}", "छूटा: {x}"), "r_tip": ("Tip: {x}", "सुझाव: {x}"),
    "err_sr": ("SpeechRecognition is not installed. Run: python -m pip install SpeechRecognition then restart Streamlit. "
               "Meanwhile you can type your answer.",
               "SpeechRecognition इंस्टॉल नहीं है। चलाएँ: python -m pip install SpeechRecognition फिर Streamlit दोबारा शुरू करें। "
               "तब तक आप उत्तर टाइप कर सकते हैं।"),
    "w_unclear": ("Could not understand the audio. Record again or type your answer.",
                  "ऑडियो समझ में नहीं आया। दोबारा रिकॉर्ड करें या उत्तर टाइप करें।"),
    "w_stt": ("Speech-to-text failed ({e}). Check your internet or type your answer.",
              "स्पीच-टू-टेक्स्ट विफल रहा ({e})। इंटरनेट जाँचें या उत्तर टाइप करें।"),
    "tts_off": ("🔇 AI voice unavailable (check your internet or install gTTS).",
                "🔇 AI की आवाज़ उपलब्ध नहीं है (इंटरनेट जाँचें या gTTS इंस्टॉल करें)।"),
    "vid_h": ("**🎥 Video answer**", "**🎥 वीडियो उत्तर**"),
    "vid_none": ("⚠️ No video was saved for this answer. Press ■ Stop & save on the video before “Check my answer”.",
                 "⚠️ इस उत्तर का वीडियो सेव नहीं हुआ। “मेरा उत्तर जाँचें” से पहले वीडियो पर ■ रोकें और सेव करें दबाएँ।"),
    "vid_dl": ("Download video", "वीडियो डाउनलोड करें"),
    "v_start": ("● Start video", "● वीडियो शुरू करें"), "v_stop": ("■ Stop & save", "■ रोकें और सेव करें"),
    "v_again": ("↻ Record again", "↻ दोबारा रिकॉर्ड करें"), "v_rec": ("● REC", "● रिकॉर्डिंग"),
    "v_saved": ("✓ Video saved", "✓ वीडियो सेव हो गया"),
    "v_err": ("Camera or microphone blocked or unavailable", "कैमरा या माइक्रोफ़ोन ब्लॉक है या उपलब्ध नहीं है"),
    "v_hint": ("Press ■ Stop & save when you finish answering.", "उत्तर पूरा होने पर ■ रोकें और सेव करें दबाएँ।"),
}


def L():
    return st.session_state.get("ui_lang", "en")


def t(key, **kw):
    s = T[key][1 if L() == "hi" else 0]
    return s.format(**kw) if kw else s


# Role knowledge (topics and tools only - the questions themselves are generated randomly each time).
ROLES = {
    "Data Analyst": {
        "about": "turns raw data into insights, reports and dashboards that help the business make decisions",
        "tools": ["SQL", "Excel", "Power BI", "Tableau", "Python", "Pandas", "Looker"],
        "topics": ["data cleaning", "SQL joins and window functions", "KPI definition", "dashboard design",
                   "A/B test analysis", "pivot tables and lookups", "data storytelling", "outlier handling",
                   "data visualization best practices", "cohort and funnel analysis", "handling missing data",
                   "report automation", "data quality checks", "trend and seasonality analysis"]},
    "AIML Engineer": {
        "about": "builds, trains, evaluates and deploys machine learning and deep learning models into production",
        "tools": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Docker", "FastAPI", "MLflow"],
        "topics": ["model training and validation", "overfitting and regularization", "deep learning architectures",
                   "feature pipelines", "model deployment and serving", "model monitoring and drift",
                   "hyperparameter tuning", "evaluation metrics", "MLOps and CI/CD", "transformers and LLMs",
                   "handling imbalanced data", "model optimization and inference speed", "experiment tracking",
                   "data leakage"]},
    "Data Scientist": {
        "about": "uses statistics, experimentation and predictive modelling to solve business problems and guide decisions",
        "tools": ["Python", "Pandas", "scikit-learn", "Jupyter", "SQL", "Matplotlib", "Statsmodels"],
        "topics": ["hypothesis testing", "feature engineering", "predictive modelling", "bias and variance",
                   "A/B testing", "regression and classification", "model evaluation", "exploratory data analysis",
                   "dimensionality reduction", "time series forecasting", "handling imbalanced data",
                   "cross-validation", "probability and distributions", "communicating model results"]},
    "Data Engineer": {
        "about": "designs and maintains the pipelines, storage and data models that deliver reliable data to analysts and models",
        "tools": ["SQL", "Python", "Airflow", "Spark", "Kafka", "Snowflake", "dbt"],
        "topics": ["ETL and ELT pipelines", "data modelling and star schema", "batch vs streaming",
                   "pipeline orchestration", "data warehouse design", "partitioning and indexing",
                   "data quality and validation", "handling schema changes", "performance tuning of queries",
                   "idempotent and fault-tolerant jobs", "data lake architecture", "change data capture",
                   "cost optimization in the cloud", "data security and governance"]},
}
# Hindi versions used only by the offline fallback (with an API key the AI writes everything in Hindi itself).
HI_ABOUT = {
    "Data Analyst": "कच्चे डेटा को ऐसी जानकारी, रिपोर्ट और डैशबोर्ड में बदलता है जो व्यवसाय को निर्णय लेने में मदद करते हैं",
    "AIML Engineer": "मशीन लर्निंग और डीप लर्निंग मॉडल बनाता, ट्रेन करता, परखता और प्रोडक्शन में तैनात करता है",
    "Data Scientist": "व्यावसायिक समस्याएँ हल करने और निर्णयों का मार्गदर्शन करने के लिए सांख्यिकी, प्रयोग और पूर्वानुमान मॉडलिंग का उपयोग करता है",
    "Data Engineer": "ऐसी पाइपलाइन, स्टोरेज और डेटा मॉडल डिज़ाइन और संचालित करता है जो विश्लेषकों और मॉडलों तक भरोसेमंद डेटा पहुँचाते हैं"}
HI_TOPICS = {
    "data cleaning": "डेटा क्लीनिंग", "SQL joins and window functions": "SQL जॉइन और विंडो फ़ंक्शन",
    "KPI definition": "KPI की परिभाषा", "dashboard design": "डैशबोर्ड डिज़ाइन", "A/B test analysis": "A/B टेस्ट का विश्लेषण",
    "pivot tables and lookups": "पिवट टेबल और लुकअप", "data storytelling": "डेटा स्टोरीटेलिंग",
    "outlier handling": "आउटलायर्स को संभालना", "data visualization best practices": "डेटा विज़ुअलाइज़ेशन की सर्वोत्तम पद्धतियाँ",
    "cohort and funnel analysis": "कोहॉर्ट और फ़नल विश्लेषण", "handling missing data": "गायब डेटा को संभालना",
    "report automation": "रिपोर्ट ऑटोमेशन", "data quality checks": "डेटा गुणवत्ता जाँच",
    "trend and seasonality analysis": "ट्रेंड और मौसमी पैटर्न का विश्लेषण",
    "model training and validation": "मॉडल ट्रेनिंग और वैलिडेशन", "overfitting and regularization": "ओवरफिटिंग और रेगुलराइज़ेशन",
    "deep learning architectures": "डीप लर्निंग आर्किटेक्चर", "feature pipelines": "फ़ीचर पाइपलाइन",
    "model deployment and serving": "मॉडल डिप्लॉयमेंट और सर्विंग", "model monitoring and drift": "मॉडल मॉनिटरिंग और ड्रिफ्ट",
    "hyperparameter tuning": "हाइपरपैरामीटर ट्यूनिंग", "evaluation metrics": "मूल्यांकन मेट्रिक्स", "MLOps and CI/CD": "MLOps और CI/CD",
    "transformers and LLMs": "ट्रांसफ़ॉर्मर और LLM", "handling imbalanced data": "असंतुलित डेटा को संभालना",
    "model optimization and inference speed": "मॉडल ऑप्टिमाइज़ेशन और इन्फ़रेंस की गति", "experiment tracking": "एक्सपेरिमेंट ट्रैकिंग",
    "data leakage": "डेटा लीकेज", "hypothesis testing": "परिकल्पना परीक्षण", "feature engineering": "फ़ीचर इंजीनियरिंग",
    "predictive modelling": "पूर्वानुमान मॉडलिंग", "bias and variance": "बायस और वैरिएंस", "A/B testing": "A/B टेस्टिंग",
    "regression and classification": "रिग्रेशन और क्लासिफ़िकेशन", "model evaluation": "मॉडल मूल्यांकन",
    "exploratory data analysis": "खोजपूर्ण डेटा विश्लेषण", "dimensionality reduction": "डायमेंशनैलिटी रिडक्शन",
    "time series forecasting": "टाइम सीरीज़ पूर्वानुमान", "cross-validation": "क्रॉस-वैलिडेशन",
    "probability and distributions": "प्रायिकता और वितरण", "communicating model results": "मॉडल के परिणाम समझाना",
    "ETL and ELT pipelines": "ETL और ELT पाइपलाइन", "data modelling and star schema": "डेटा मॉडलिंग और स्टार स्कीमा",
    "batch vs streaming": "बैच बनाम स्ट्रीमिंग", "pipeline orchestration": "पाइपलाइन ऑर्केस्ट्रेशन",
    "data warehouse design": "डेटा वेयरहाउस डिज़ाइन", "partitioning and indexing": "पार्टिशनिंग और इंडेक्सिंग",
    "data quality and validation": "डेटा गुणवत्ता और वैलिडेशन", "handling schema changes": "स्कीमा बदलावों को संभालना",
    "performance tuning of queries": "क्वेरी का परफ़ॉर्मेंस ट्यूनिंग", "idempotent and fault-tolerant jobs": "आइडेम्पोटेंट और फ़ॉल्ट-टॉलरेंट जॉब्स",
    "data lake architecture": "डेटा लेक आर्किटेक्चर", "change data capture": "चेंज डेटा कैप्चर",
    "cost optimization in the cloud": "क्लाउड में लागत अनुकूलन", "data security and governance": "डेटा सुरक्षा और गवर्नेंस"}
# Only used when no API key is available: questions are assembled randomly from the topics and tools above.
TECH_T = ["Explain {t} and how you would apply it as a {r}.",
          "What common mistakes happen with {t}, and how do you avoid them?",
          "Walk me through how you would use {tool} for {t}.",
          "How would you check that your work on {t} is correct?",
          "When would you choose {tool} for {t}, and what are the trade-offs?"]
BEH_T = ["Tell me about a time you worked on {t}. What was the situation, your action and the result?",
         "Describe a mistake you made while working on {t}. What did you learn?",
         "Tell me about a time you had to explain {t} to a non-technical stakeholder.",
         "Describe a tight deadline involving {t} and how you handled it.",
         "Tell me about a disagreement with a teammate about {t}. How was it resolved?"]
TECH_HI = ["{t} को समझाइए और बताइए कि एक {r} के रूप में आप इसे कैसे लागू करेंगे।",
           "{t} में आम तौर पर कौन-सी गलतियाँ होती हैं, और आप उनसे कैसे बचते हैं?",
           "{t} के लिए आप {tool} का उपयोग कैसे करेंगे, यह चरण-दर-चरण बताइए।",
           "आप कैसे जाँचेंगे कि {t} पर आपका काम सही है?",
           "{t} के लिए आप {tool} कब चुनेंगे, और इसके क्या फायदे-नुकसान हैं?"]
BEH_HI = ["किसी ऐसे समय के बारे में बताइए जब आपने {t} पर काम किया। स्थिति क्या थी, आपने क्या किया और परिणाम क्या रहा?",
          "{t} पर काम करते समय हुई किसी गलती का वर्णन कीजिए। आपने उससे क्या सीखा?",
          "किसी ऐसे समय के बारे में बताइए जब आपको {t} किसी गैर-तकनीकी व्यक्ति को समझाना पड़ा।",
          "{t} से जुड़ी किसी कड़ी समय-सीमा का वर्णन कीजिए और बताइए कि आपने उसे कैसे संभाला।",
          "{t} को लेकर किसी सहकर्मी से हुई असहमति के बारे में बताइए। उसका समाधान कैसे हुआ?"]

# Small live camera preview (no capture button, nothing is saved or uploaded) - used on the feedback screen.
CAM_HTML = """<style>html,body{margin:0;background:transparent}
video{width:100%;height:135px;border-radius:12px;object-fit:cover;transform:scaleX(-1);background:#111}
#m{font:12px sans-serif;color:#888;text-align:center}</style>
<video id="v" autoplay muted playsinline></video><div id="m"></div>
<script>navigator.mediaDevices.getUserMedia({video:true}).then(s=>{v.srcObject=s})
.catch(()=>{m.textContent="Camera blocked or unavailable"})</script>"""

# Live preview + automatic video recording (MediaRecorder). Sends the finished video back to Python when the user
# presses "Stop & save". A tiny custom Streamlit component: plain HTML/JS, no build step.
VIDEO_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent;font:12px system-ui,sans-serif;color:#888}
video{width:100%;height:135px;border-radius:12px;object-fit:cover;transform:scaleX(-1);background:#111;display:block}
button{width:100%;margin-top:6px;padding:6px;border-radius:8px;border:1px solid #d33;background:transparent;color:#d33;
font:600 13px system-ui,sans-serif;cursor:pointer}button:disabled{opacity:.5;cursor:default}
#s{margin-top:4px;text-align:center}.r{color:#d33;font-weight:600}</style></head><body>
<video id="v" autoplay muted playsinline></video><button id="b" disabled>…</button><div id="s"></div>
<script>
var A={labels:{},autostart:true},stream=null,rec=null,chunks=[],state="init",started=false,t0=0,tm=null,mime="";
function post(o){o.isStreamlitMessage=true;window.parent.postMessage(o,"*")}
function ui(){var b=document.getElementById("b"),s=document.getElementById("s"),l=A.labels||{};
 b.disabled=(state==="init"||state==="err"||state==="saving");
 b.textContent=state==="rec"?l.v_stop:(state==="saved"?l.v_again:l.v_start);
 s.className=state==="rec"?"r":"";
 s.textContent=state==="rec"?(l.v_rec+" "+Math.round((Date.now()-t0)/1000)+"s"):(state==="saved"?l.v_saved:(state==="err"?l.v_err:l.v_hint))}
function start(){var ty=["video/webm;codecs=vp8,opus","video/webm","video/mp4"];mime="";
 for(var i=0;i<ty.length;i++){if(window.MediaRecorder&&MediaRecorder.isTypeSupported(ty[i])){mime=ty[i];break}}
 chunks=[];rec=new MediaRecorder(stream,mime?{mimeType:mime,videoBitsPerSecond:700000}:{});
 rec.ondataavailable=function(e){if(e.data&&e.data.size){chunks.push(e.data)}};
 rec.onstop=finish;rec.start(1000);t0=Date.now();state="rec";clearInterval(tm);tm=setInterval(ui,1000);ui()}
function finish(){clearInterval(tm);state="saving";ui();
 var type=((rec&&rec.mimeType)||mime||"video/webm").split(";")[0],blob=new Blob(chunks,{type:type}),fr=new FileReader();
 fr.onload=function(){post({type:"streamlit:setComponentValue",dataType:"json",
  value:{mime:type,data:String(fr.result).split(",")[1],seconds:Math.round((Date.now()-t0)/1000)}});state="saved";ui()};
 fr.readAsDataURL(blob)}
function init(){var md=navigator.mediaDevices;
 function ok(s){stream=s;document.getElementById("v").srcObject=s;state="idle";ui();if(A.autostart){start()}}
 function bad(){state="err";ui()}
 if(!md||!md.getUserMedia){bad();return}
 md.getUserMedia({video:{width:{ideal:640},height:{ideal:480}},audio:true}).then(ok).catch(function(){
  md.getUserMedia({video:true}).then(ok).catch(bad)})}
document.getElementById("b").onclick=function(){if(state==="rec"){rec.stop()}else if(stream){start()}};
window.addEventListener("message",function(e){var d=e.data;
 if(d&&d.type==="streamlit:render"){A=d.args||A;ui();if(!started){started=true;init()}}});
window.addEventListener("pagehide",function(){if(stream){stream.getTracks().forEach(function(x){x.stop()})}});
post({type:"streamlit:componentReady",apiVersion:1});post({type:"streamlit:setFrameHeight",height:205});ui();
</script></body></html>"""


@st.cache_resource
def _video_component():
    import streamlit.components.v1 as components
    d = os.path.join(tempfile.gettempdir(), "aic_video_" + hashlib.md5(VIDEO_HTML.encode()).hexdigest()[:10])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(VIDEO_HTML)
    return components.declare_component("aic_video_recorder", path=d)


def video_recorder(key):
    labels = {k: t(k) for k in ("v_start", "v_stop", "v_again", "v_rec", "v_saved", "v_err", "v_hint")}
    return _video_component()(labels=labels, autostart=True, key=key, default=None)


def show_camera():
    if hasattr(st, "iframe"):  # newer Streamlit
        st.iframe(CAM_HTML, height=150)
    else:  # older Streamlit
        import streamlit.components.v1 as components
        components.html(CAM_HTML, height=150)


# ---------- AI helpers ----------
def api_key():
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def llm_json(prompt):
    key = api_key()
    if not key:
        return None
    try:
        import anthropic
        msg = anthropic.Anthropic(api_key=key).messages.create(
            model=MODEL, max_tokens=4000, messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.strip().strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:]
        return json.loads(text)
    except Exception:
        return None


def make_questions(c):
    """Q1 = introduction + role of the field. Q2-Q10 follow the chosen scenario and differ every time."""
    role, sc, info = c["role"], c["scenario"], ROLES[c["role"]]
    topics = random.sample(info["topics"], 9)
    kinds = {"Technical": ["tech"] * 9, "Behavioral": ["beh"] * 9}.get(sc) or random.sample(["tech"] * 5 + ["beh"] * 4, 9)
    rule = {"Technical": "ALL 9 questions must be technical: concepts, tools and practical problem solving (no coding on screen).",
            "Behavioral": "ALL 9 questions must be behavioral (STAR style: tell me about a time...) about real work situations in this field.",
            "Standard": "5 questions technical and 4 behavioral, in mixed order."}[sc]
    data = llm_json(
        f'Create a mock interview of exactly 10 questions for a {role} ({c["level"]}). Extra details: {c["details"] or "none"}. '
        f'Write everything in {c["lang_name"]}. Question 1 must ask the candidate to introduce themselves and explain what the '
        f'role of a {role} is. Questions 2-10: {rule} Base them on the field and its tools ({", ".join(info["tools"])}); '
        f'use these focus topics, one per question: {"; ".join(topics)}. Make fresh, varied questions (random seed '
        f'{random.randint(1, 10**6)}). Return ONLY a JSON array of 10 objects {{"q":question,"ideal":model answer in 2-4 '
        f'sentences,"keywords":[5-8 key points an ideal answer must mention]}}.')
    if isinstance(data, list) and len(data) >= 10 and all(isinstance(d, dict) and "q" in d and "ideal" in d for d in data):
        for d in data:
            d.setdefault("keywords", [])
        return data[:10], False
    tools = info["tools"]
    hi = L() == "hi"
    if hi:
        rn = t(role)
        qs = [{"q": f"कृपया अपना परिचय दीजिए, फिर बताइए कि एक {rn} क्या करता है और आप इस क्षेत्र में काम क्यों करना चाहते हैं।",
               "ideal": f"एक अच्छा उत्तर आपकी पृष्ठभूमि और कौशल का परिचय देता है, फिर बताता है कि {rn} {HI_ABOUT[role]}, "
                        f"और {', '.join(tools[:4])} जैसे टूल्स का उल्लेख करता है।",
               "keywords": ["अनुभव", "कौशल"] + [x.lower() for x in tools[:4]]}]
        tech, beh = random.sample(TECH_HI, 5), random.sample(BEH_HI, 5)
    else:
        qs = [{"q": f"Please introduce yourself, then explain what a {role} does and why you want to work in this field.",
               "ideal": f"A strong answer introduces your background and skills, then explains that a {role} {info['about']}, "
                        f"mentioning tools such as {', '.join(tools[:4])}.",
               "keywords": ["experience", "skills"] + [x.lower() for x in tools[:4]]}]
        tech, beh = random.sample(TECH_T, 5), random.sample(BEH_T, 5)
    for n, (tp, kind) in enumerate(zip(topics, kinds)):
        tool = random.choice(tools)
        name = HI_TOPICS.get(tp, tp) if hi else tp
        words = [w for w in name.lower().split() if len(w) > 3]
        if kind == "tech":
            if hi:
                q = tech[n % 5].format(t=name, r=t(role), tool=tool)
                ideal = f"एक अच्छा उत्तर {name} को समझाता है, दिखाता है कि {tool} का उपयोग कैसे होता है, एक ठोस उदाहरण देता है और संभावित गलतियों का उल्लेख करता है।"
                kw = words + [tool.lower(), "उदाहरण"]
            else:
                q = tech[n % 5].format(t=name, r=role, tool=tool)
                ideal = f"A strong answer explains {name}, shows how {tool} is used, gives a concrete example and mentions pitfalls."
                kw = words + [tool.lower(), "example"]
        else:
            if hi:
                q = beh[n % 5].format(t=name)
                ideal = f"{name} पर एक अच्छा STAR उत्तर: स्पष्ट स्थिति, आपका कार्य, आपकी कार्रवाई और मापने योग्य परिणाम।"
                kw = ["स्थिति", "कार्य", "कार्रवाई", "परिणाम", "सीखा"] + words
            else:
                q = beh[n % 5].format(t=name)
                ideal = f"A strong STAR answer about {name}: clear situation, your task, the action you took and a measurable result."
                kw = ["situation", "action", "result", "learned"] + words
        qs.append({"q": q, "ideal": ideal, "keywords": kw})
    return qs, True


def local_eval(q, ans):
    # Offline fallback: keyword coverage only; this is not semantic AI grading.
    kw = [k.lower() for k in q.get("keywords", [])]
    low = ans.lower()
    hit = [k for k in kw if k in low]
    miss = [k for k in kw if k not in hit]
    match = round(100 * len(hit) / len(kw)) if ans.strip() and kw else (20 if ans.strip() else 0)
    tip = t("le_tip")
    return {
        "match": match, "covered": hit, "missing": miss,
        "strengths": [t("le_rel", x=", ".join(hit[:4]))] if hit else [t("le_try")],
        "faults": [t("le_nopts", x=", ".join(miss[:4]))] if miss else [t("le_nogap")],
        "tip": tip,
        "spoken": (t("le_spm", x=", ".join(miss[:2])) if miss else t("le_spo")) + tip
    }


def evaluate(q, ans, c):
    res = llm_json(
        f'You are a strict but kind interview coach for "{c["role"]}" ({c["level"]}). Question: {q["q"]}\n'
        f'Ideal answer: {q["ideal"]}\nKey points: {", ".join(q.get("keywords", []))}\n'
        f'Candidate answer (speech transcript, may contain small errors): {ans}\n'
        f'Judge by meaning, not exact words. Apply this 10-mark rubric: {json.dumps(c.get("rubric", {}))}. Write text in {c["lang_name"]}. Return ONLY JSON: {{"match":0-100,'
        '"covered":[key points covered],"missing":[key points missed],"strengths":[1-3 strings],'
        '"faults":[1-3 strings],"tip":"one improvement","spoken":"2-3 sentence spoken feedback naming the main fault"}')
    try:
        m = max(0, min(100, int(res["match"])))
        for k in ("covered", "missing", "strengths", "faults"):
            res[k] = [str(x) for x in res.get(k, [])]
        res.setdefault("tip", "")
        res.setdefault("spoken", res["tip"])
    except Exception:
        res = local_eval(q, ans)
        m = res["match"]
    res.update(match=m, score=round(m / 10),
               verdict=t("v_ok") if m >= 75 else t("v_part") if m >= 40 else t("v_bad"))
    return res


# ---------- voice helpers ----------
def transcribe(wav_bytes, lang):
    try:
        import speech_recognition as sr
    except ImportError:
        st.error(t("err_sr"))
        return ""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(wav_bytes)) as src:
            audio = r.record(src)
        return r.recognize_google(audio, language=lang)
    except sr.UnknownValueError:
        st.warning(t("w_unclear"))
    except Exception as e:
        st.warning(t("w_stt", e=e))
    return ""


@st.cache_data(show_spinner=False)
def tts(text, lang):
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text, lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def speak(text, lang, autoplay=True):
    audio = tts(text, lang)
    if audio:
        st.audio(audio, format="audio/mp3", autoplay=autoplay)
    else:
        st.caption(t("tts_off"))


def show_video(col, r, n=None):
    """Show the saved video of an answer (or a hint if none was saved)."""
    if r.get("video"):
        col.markdown(t("vid_h"))
        col.video(r["video"], format=r.get("video_mime", "video/webm"))
        if n:
            ext = "mp4" if "mp4" in r.get("video_mime", "") else "webm"
            col.download_button(t("vid_dl"), r["video"], f"answer_{n}.{ext}", r.get("video_mime", "video/webm"), key=f"dlv{n}")
    elif r.get("cam_on"):
        col.caption(t("vid_none"))


# ---------- screens ----------
def setup_screen():
    ss = st.session_state
    ss["ui_lang"] = ss.get("lang_pick", ss.get("ui_lang", "en"))
    st.title(t("title"))
    st.caption(t("sub"))
    with st.container(border=True):
        c1, c2 = st.columns(2)
        role = c1.selectbox(t("role"), list(ROLES), format_func=t, key="f_role")
        level = c2.selectbox(t("level"), ["Entry-level", "Mid-level", "Senior"], format_func=t, key="f_level")
        scenario = c1.selectbox(t("scen"), ["Standard", "Technical", "Behavioral"], format_func=t, help=t("scen_help"), key="f_scen")
        code = c2.selectbox("Interview language / इंटरव्यू की भाषा", list(LANG_NAMES), format_func=LANG_NAMES.get, key="lang_pick")
        skills = st.text_input(t("skills"), placeholder=t("skills_ph"), key="f_skills")
        company = st.text_input(t("company"), key="f_company")
        job_description = st.text_area(t("jd"), height=90, key="f_jd")
        focus_topics = st.text_area(t("focus"), key="f_focus")
        details = "\n".join(x for x in [
            f"Skills: {skills}" if skills else "",
            f"Company: {company}" if company else "",
            f"Job description: {job_description}" if job_description else "",
            f"Focus topics: {focus_topics}" if focus_topics else ""
        ] if x)
        st.markdown(t("rub_h"))
        rc1, rc2 = st.columns(2)
        rubric = {
            "Technical accuracy": rc1.number_input(t("Technical accuracy"), 0, 10, 4, key="f_r1"),
            "Explanation and structure": rc2.number_input(t("Explanation and structure"), 0, 10, 2, key="f_r2"),
            "Practical example": rc1.number_input(t("Practical example"), 0, 10, 2, key="f_r3"),
            "Communication": rc2.number_input(t("Communication"), 0, 10, 2, key="f_r4")
        }
        st.caption(t("rub_tot", n=sum(rubric.values())))
        mic_consent = st.checkbox(t("mic_c"), key="f_mic")
        camera = st.checkbox(t("cam_c"), key="f_cam")
        go = st.button(t("gen"), type="primary")
    if go:
        if sum(rubric.values()) != 10:
            st.error(t("err_rub"))
            return
        if not mic_consent:
            st.error(t("err_mic"))
            return
        stt_code, tts_code, lang_name = LANGS[code]
        cfg = dict(role=role, level=level, scenario=scenario, details=details.strip(), lang_name=lang_name,
                   stt=stt_code, tts=tts_code, camera=camera,
                   mic_consent=mic_consent, rubric=rubric, company=company)
        with st.spinner(t("spin_gen")):
            qs, fallback = make_questions(cfg)
        st.session_state.update(stage="interview", cfg=cfg, qs=qs, fallback=fallback, i=0, phase="answer",
                                results=[], played=set())
        st.rerun()


def interview_screen():
    ss, c = st.session_state, st.session_state.cfg
    i, q = ss.i, ss.qs[ss.i]
    st.progress(i / 10, text=t("prog", n=i + 1, role=t(c["role"]), sc=t(c["scenario"])))
    left, right = st.columns([3, 1] if c["camera"] else [1, 0.001])
    left.subheader(q["q"])
    video = None
    if c["camera"]:
        with right:
            st.caption(t("cam_prev"))
            if ss.phase == "answer":
                video = video_recorder(f"vid{i}")  # live preview + automatic video recording
            else:
                show_camera()
    if ss.phase == "answer":
        with left:
            speak(q["q"], c["tts"], autoplay=i not in ss.played)
        ss.played.add(i)
        audio = st.audio_input(t("mic"), key=f"mic{i}")
        if audio is not None:
            data = audio.getvalue()
            if ss.get(f"h{i}") != hash(data):
                ss[f"h{i}"] = hash(data)
                with st.spinner(t("spin_stt")):
                    ss[f"t{i}"] = transcribe(data, c["stt"])
        ans = st.text_area(t("ans_lbl"), key=f"t{i}", height=130)
        if st.button(t("check"), type="primary"):
            if not ans.strip():
                st.warning(t("warn_empty"))
                return
            with st.spinner(t("spin_cmp")):
                res = evaluate(q, ans, c)
            vid = video if isinstance(video, dict) and video.get("data") else None
            res.update(q=q["q"], ideal=q["ideal"], answer=ans, audio=audio.getvalue() if audio else None,
                       video=base64.b64decode(vid["data"]) if vid else None,
                       video_mime=vid["mime"] if vid else "video/webm", cam_on=c["camera"],
                       evaluation_mode="AI meaning-based" if api_key() else "Offline keyword heuristic")
            ss.results.append(res)
            ss.phase = "feedback"
            st.rerun()
        if ss.fallback:
            st.caption(t("fb_note"))
    else:
        r = ss.results[-1]
        a, b = st.columns(2)
        a.markdown(t("your"))
        a.info(r["answer"])
        if r["audio"]:
            a.audio(r["audio"], format="audio/wav")
        show_video(a, r)
        b.markdown(t("ideal"))
        b.success(r["ideal"])
        m1, m2, m3 = st.columns(3)
        m1.metric(t("m_match"), f'{r["match"]}%')
        m2.metric(t("m_score"), f'{r["score"]}/10')
        m3.metric(t("m_verd"), r["verdict"])
        st.progress(r["match"] / 100)
        x, y = st.columns(2)
        x.markdown(t("cov") + "\n\n" + ("\n".join(f"- {s}" for s in r["covered"]) or "- " + t("none_yet")))
        y.markdown(t("mis") + "\n\n" + ("\n".join(f"- {s}" for s in r["missing"]) or "- " + t("nothing")))
        st.markdown(t("stre") + "\n\n" + "\n".join(f"- {s}" for s in r["strengths"]))
        st.markdown(t("impr") + "\n\n" + "\n".join(f"- {s}" for s in r["faults"]))
        st.markdown(t("tipl", x=r["tip"]))
        speak(r["spoken"], c["tts"])
        if st.button(t("view") if i == 9 else t("nextq"), type="primary"):
            if i == 9:
                ss.stage = "report"
            else:
                ss.i, ss.phase = i + 1, "answer"
            st.rerun()


def report_screen():
    ss, c = st.session_state, st.session_state.cfg
    rs = ss.results
    total = sum(r["score"] for r in rs)
    band = t("b1") if total >= 80 else t("b2") if total >= 60 else t("b3") if total >= 40 else t("b4")
    st.title(t("rep_t"))
    st.caption(f'{t(c["role"])} · {t(c["level"])} · {t(c["scenario"])} · {datetime.now():%d %b %Y, %H:%M}')
    k1, k2 = st.columns(2)
    k1.metric(t("rep_tot"), f"{total} / 100")
    k2.metric(t("rep_avg"), f'{round(sum(r["match"] for r in rs) / len(rs))}%')
    st.subheader(band)
    df = pd.DataFrame([{t("c_q"): n + 1, t("c_question"): r["q"], t("c_match"): r["match"], t("c_score"): r["score"],
                        t("c_verd"): r["verdict"]} for n, r in enumerate(rs)])
    st.dataframe(df, hide_index=True)
    weak = sorted(rs, key=lambda r: r["score"])[:3]
    st.markdown(t("rec_h") + "\n\n" + "\n".join(t("rec_rev", x=r["q"]) for r in weak) + "\n" + t("rec_pr"))
    for n, r in enumerate(rs, 1):
        with st.expander(t("exp", n=n, s=r["score"], m=r["match"], v=r["verdict"])):
            st.markdown(t("q_l", x=r["q"]))
            a, b = st.columns(2)
            a.markdown(t("your"))
            a.info(r["answer"])
            if r["audio"]:
                a.audio(r["audio"], format="audio/wav")
            show_video(a, r, n)
            b.markdown(t("ideal"))
            b.success(r["ideal"])
            st.markdown(t("miss_l", x=", ".join(r["missing"]) or t("nothing2"), tip=r["tip"]))
    txt = f'{t("r_head")}\n{t(c["role"])} | {t(c["level"])} | {t(c["scenario"])}\n{t("r_score", t=total, b=band)}\n\n' + "\n".join(
        f'{t("r_q", n=n, s=r["score"], m=r["match"], v=r["verdict"], q=r["q"])}\n{t("r_ans", x=r["answer"])}\n'
        f'{t("r_ideal", x=r["ideal"])}\n{t("r_mis", x=", ".join(r["missing"]))}\n{t("r_tip", x=r["tip"])}\n'
        for n, r in enumerate(rs, 1))
    d1, d2 = st.columns(2)
    d1.download_button(t("dl_txt"), txt, "interview_report.txt")
    d2.download_button(t("dl_csv"), df.to_csv(index=False), "interview_scores.csv")
    if st.button(t("new")):
        lang = ss.get("ui_lang", "en")
        st.session_state.clear()
        st.session_state["ui_lang"] = st.session_state["lang_pick"] = lang
        st.rerun()


st.set_page_config(page_title="AI Interview Coach", page_icon="🎙️", initial_sidebar_state="collapsed")
st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
            "[data-testid='collapsedControl']{display:none}</style>",
            unsafe_allow_html=True)
{"setup": setup_screen, "interview": interview_screen, "report": report_screen}[st.session_state.get("stage", "setup")]()