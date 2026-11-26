"""The Hebrew chat. Shows only final answers; drafts and feedback go to logs/chat_log.jsonl."""

import gradio as gr

from pipeline import answer_question


def chat(message, history):
    shown, record = answer_question(message, history)
    print(f"[{record['end_state']}] {len(record['attempts'])} attempt(s) | {message}", flush=True)
    return shown


if __name__ == "__main__":
    gr.ChatInterface(
        fn=chat,
        title="התאום הדיגיטלי של נעמה ינובסקי",
        description="שאלו אותי על הלימודים, הניסיון, המיומנויות והפרויקטים שלי. כל תשובה נבדקת לפני שהיא מוצגת.",
        chatbot=gr.Chatbot(rtl=True, height=480),
        textbox=gr.Textbox(placeholder="כתבו כאן שאלה...", rtl=True),
        examples=["איפה את לומדת ובאיזה מסלול?", "מה עשית בשירות הצבאי?", "באילו שפות תכנות את עובדת?"],
    ).launch()
