from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import logging
import random
import string

load_dotenv()


app = Flask(__name__)
app.secret_key = "your_secret_key"

# تنظیمات ایمیل
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False  # این مقدار باید False باشد
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")  
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

# تولید کد OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# صفحه فرم تماس
@app.route("/", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        lname = request.form.get("lname", "").strip()
        email = request.form.get("email", "").strip()
        age = request.form.get("age", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()
        honeypot = request.form.get("honeypot", "").strip()  # فیلد مخفی

        # بررسی فیلد فریب ربات
        if honeypot:
            logging.warning("Robot Attempt Recognized")
            flash("Robot attempt error", "danger")
            return redirect(url_for("contact"))

        # بررسی فیلدهای اجباری
        if not name or not email or not message or not lname or not age:
            flash("لطفاً همه‌ی فیلدها را پر کنید!", "danger")
            return redirect(url_for("contact"))

        # ذخیره اطلاعات در session
        session["form_data"] = {
            "name": name,
            "lname": lname,
            "email": email,
            "age": age,
            "phone": phone,
            "message": message
        }

        # ارسال کد OTP
        otp = generate_otp()
        session["otp"] = otp

        msg = Message("کد تأیید شما", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = f"کد تأیید شما: {otp}"

        try:
            mail.send(msg)
            flash("کد تأیید به ایمیل شما ارسال شد!", "success")
            return redirect(url_for("verify_otp"))
        except Exception as e:
            flash("خطایی در ارسال ایمیل رخ داد!", "danger")
            logging.error(f"خطای ایمیل: {e}")

    return render_template("contact.html")

# صفحه تأیید کد OTP
@app.route("/verify", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form.get("otp", "").strip()

        if user_otp == session.get("otp"):
            flash("ایمیل شما تأیید شد.", "success")

            # ارسال پیام نهایی به ایمیل مدیر
            form_data = session.get("form_data", {})
            msg = Message(
                "پیام جدید از فرم تماس",
                sender=app.config["MAIL_USERNAME"],
                recipients=["behbood2008@gmail.com", "behrayanics@gmail.com"]
            )
            msg.body = f"""فرستنده: {form_data.get("name")} {form_data.get("lname")}
سن: {form_data.get("age")}
ایمیل: {form_data.get("email")}
تلفن: {form_data.get("phone")}

پیام:
{form_data.get("message")}
"""

            try:
                mail.send(msg)
                flash("پیام شما با موفقیت ارسال شد!", "success")
                session.pop("form_data")  # پاک کردن اطلاعات فرم
                session.pop("otp")  # پاک کردن کد OTP
                return redirect(url_for("contact"))
            except Exception as e:
                logging.error(f"خطا در ارسال ایمیل: {e}")
                flash("متأسفیم! خطایی در ارسال ایمیل رخ داد.", "danger")
                return redirect(url_for("contact"))
        else:
            flash("کد تأیید اشتباه است! دوباره امتحان کنید.", "danger")

    return render_template("verify_otp.html")
    
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
