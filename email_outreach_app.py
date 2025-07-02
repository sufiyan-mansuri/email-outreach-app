import streamlit as st
import pandas as pd
import yagmail
import time
import random
import openai

# --- Constants ---
gmail_user = st.secrets["gmail_user"]
gmail_app_password = st.secrets["gmail_app_password"]
openai_api_key = st.secrets["openai_api_key"]

# --- UI Layout ---
st.title("📺 YouTube Creator Outreach")

uploaded_file = st.file_uploader("Upload your YouTube leads CSV", type=["csv"])

# --- Subject Line Generation Function ---
def generate_subject(channel_name, traits, api_key):
    openai.api_key = api_key

    prompt = f"""
You are an expert cold email copywriter helping a professional video editor pitch their services to YouTube creators.

Generate 5 catchy and personalized email subject lines for a cold outreach message offering video editing services. These subject lines should be attention-grabbing, natural, and make the recipient want to open the email.

Tone: Friendly, confident, scroll-stopping — not too formal or too casual.  
Avoid using quotation marks.  
Keep each subject line under 12 words.  
Include the variable [channel_name] naturally in each line.  
Use the provided creator traits to personalize the messaging tone and angle.

Variables:
- channel_name = {channel_name}
- traits = {traits}

Output only the 5 subject lines as a list, no explanations.
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_subjects = response['choices'][0]['message']['content']
    lines = [line.strip("-•* 1234567890.} ").strip('"').strip("'") for line in raw_subjects.split("\n") if line.strip()]
    clean_lines = [line.replace("[channel_name]", channel_name) for line in lines if "[channel_name]" in line or channel_name in line]
    subject = random.choice(clean_lines) if clean_lines else f"Video idea for {channel_name}"
    return subject

# --- Email Generation Function ---
def generate_email(channel_name, about_us, subscribers, api_key):
    openai.api_key = api_key

    prompt = f"""
You're a professional video editor named Aimaan reaching out to YouTube creators.

Generate a short, casual outreach email body based on this info. Structure it into exactly 3 paragraphs:

1. Compliment the creator's content based on their description.
2. Introduce yourself as Aimaan, a video editor with 2B+ views.
3. Offer to do one free edit, mention your site (aimaanedits.com), and invite collaboration.

❌ Do NOT include any closing line like "Looking forward..." or "Would be dope to connect."
❌ Do NOT sign off with your name or use "Best" — leave that for the fixed footer.

Just return the 3 paragraphs only.

Details:
Channel Name: {channel_name}
About Us: {about_us}
Subscribers: {subscribers}
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    body = response['choices'][0]['message']['content'].strip()

    # Normalize paragraph spacing to exactly 1 break
    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
    body_clean = "\n\n".join(paragraphs)

    # Original footer (no HTML)
    footer = """
Best,
Aimaan
<a href="https://www.instagram.com/aimaanedits" target="_blank">Instagram</a>
"""

    final_body = body_clean.replace("\n", "<br>") + "<br><br>" + footer
    return final_body

# --- Email Sending ---
if st.button("🚀 Start Sending Emails"):
    if not uploaded_file:
        st.error("⚠️ Please upload your YouTube leads CSV.")
        st.stop()

    try:
        df = pd.read_csv(uploaded_file)
        yag = yagmail.SMTP(gmail_user, gmail_app_password)
        sent_count = 0

        for idx, row in df.iterrows():
            email = row.get("email") or row.get("Email")
            channel_name = row.get("Channel Name") or "there"
            about_us = row.get("About Us") or "a great creator"
            subscribers = row.get("Subscribers") or "unknown"

            if not email or "@" not in str(email):
                st.warning(f"⚠️ Skipping row {idx} — invalid email.")
                continue

            try:
                email_content = generate_email(channel_name, about_us, subscribers, openai_api_key)
                traits = row.get("Traits") or "creative, passionate, confident, consistent, engaging"
                subject = generate_subject(channel_name, traits, openai_api_key)
                yag.send(to=email, subject=subject, contents=[email_content])
                st.success(f"✅ Sent to {email}")
                sent_count += 1
                time.sleep(random.randint(40, 90))

            except Exception as e:
                st.error(f"❌ Failed to send to {email}: {e}")

        st.info(f"🎉 Finished — {sent_count} emails sent!")

    except Exception as e:
        st.error(f"❌ Failed to process file or send emails: {e}")
