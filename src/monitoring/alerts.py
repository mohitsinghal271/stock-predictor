"""
src/monitoring/alerts.py

Phase 14M: Resilient Multi-Channel Alerting System for NSE Autonomous Paper Trading.
Channels supported:
1. File append: reports/paper_trading/ALERTS.log
2. Telegram Bot (via TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
3. Email / SMTP (via SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO)
4. WhatsApp (via CallMeBot CALLMEBOT_PHONE, CALLMEBOT_API_KEY OR Twilio TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, WHATSAPP_TO)
5. Generic Webhook (via ALERT_WEBHOOK_URL)
6. Structured Console Logger

All calls are non-blocking / fail-safe (wrapped in try/except) so alerting never crashes
the core trading engine.
"""

import os
import json
import logging
import smtplib
import urllib.parse
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("AlertManager")

class AlertManager:
    """Manages paper trading system alerts, warnings, and multi-channel notifications."""

    def __init__(self, log_path: str = "reports/paper_trading/ALERTS.log"):
        self.log_path = log_path
        
        # 1. Telegram
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # 2. Email / SMTP
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.email_to = os.getenv("ALERT_EMAIL_TO")
        self.email_from = os.getenv("ALERT_EMAIL_FROM", self.smtp_user)

        # 3. WhatsApp (CallMeBot or Twilio)
        self.callmebot_phone = os.getenv("CALLMEBOT_PHONE") # format: +919876543210
        self.callmebot_key = os.getenv("CALLMEBOT_API_KEY")
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.getenv("TWILIO_WHATSAPP_FROM") # e.g. whatsapp:+14155238886
        self.whatsapp_to = os.getenv("WHATSAPP_TO")           # e.g. whatsapp:+919876543210

        # 4. Webhook
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def send_alert(self, level: str, title: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Send an alert across all configured channels.
        level: 'INFO', 'WARNING', 'CRITICAL', 'TRADE', 'RISK'
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "title": title,
            "message": message,
            "metadata": metadata or {}
        }

        # 1. Console Log
        if level in ["CRITICAL", "RISK"]:
            logger.error(f"[{level}] {title}: {message}")
        elif level == "WARNING":
            logger.warning(f"[{level}] {title}: {message}")
        else:
            logger.info(f"[{level}] {title}: {message}")

        # 2. Append to ALERTS.log
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level:8s}] {title}: {message} | data={json.dumps(metadata or {})}\n")
        except Exception as e:
            logger.error(f"Failed to append to alert log: {e}")

        # 3. Webhook (if configured)
        if self.webhook_url:
            self._send_webhook(log_entry)

        # 4. Telegram (if configured)
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(level, title, message)

        # 5. Email (if configured)
        if self.smtp_host and self.smtp_user and self.smtp_pass and self.email_to:
            self._send_email(level, title, message, log_entry)

        # 6. WhatsApp (if configured)
        if self.callmebot_phone and self.callmebot_key:
            self._send_whatsapp_callmebot(level, title, message)
        elif self.twilio_sid and self.twilio_token and self.twilio_from and self.whatsapp_to:
            self._send_whatsapp_twilio(level, title, message)

    def _send_webhook(self, payload: Dict[str, Any]):
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception as e:
            logger.debug(f"Webhook dispatch failed: {e}")

    def _send_telegram(self, level: str, title: str, message: str):
        try:
            emoji = self._get_emoji(level)
            text = f"{emoji} *[{level}] {title}*\n{message}\n_Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = json.dumps({"chat_id": self.telegram_chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception as e:
            logger.debug(f"Telegram dispatch failed: {e}")

    def _send_email(self, level: str, title: str, message: str, payload: Dict[str, Any]):
        """Send alert email via SMTP (e.g. Gmail, Outlook, AWS SES)."""
        try:
            emoji = self._get_emoji(level)
            subject = f"{emoji} [{level}] {title} - NSE Quant Engine"

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = self.email_to

            # Plain text version
            text_body = f"{subject}\n\nTime: {payload['timestamp']}\nLevel: {level}\n\n{message}\n\nMetadata: {json.dumps(payload['metadata'], indent=2)}"
            
            # HTML version
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="background-color: #0f172a; color: #fff; padding: 16px; border-radius: 8px;">
                    <h2 style="margin: 0; color: #38bdf8;">{emoji} [{level}] {title}</h2>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px;">NSE Autonomous Paper Trading Engine | {payload['timestamp']}</p>
                </div>
                <div style="padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 12px;">
                    <p style="font-size: 15px; font-weight: 500;">{message}</p>
                    {f'<pre style="background: #e2e8f0; padding: 10px; border-radius: 6px; font-size: 12px;">{json.dumps(payload["metadata"], indent=2)}</pre>' if payload.get('metadata') else ''}
                </div>
                <p style="font-size: 11px; color: #64748b; margin-top: 16px;">This is an automated alert from your autonomous NSE trading research system.</p>
            </body>
            </html>
            """

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Connect via SSL or TLS
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.email_from, [self.email_to], msg.as_string())
            server.quit()
            logger.info(f"Email alert sent successfully to {self.email_to}")
        except Exception as e:
            logger.debug(f"Email dispatch failed: {e}")

    def _send_whatsapp_callmebot(self, level: str, title: str, message: str):
        """Send WhatsApp message via CallMeBot (instant setup for personal WhatsApp)."""
        try:
            emoji = self._get_emoji(level)
            text = f"{emoji} *[{level}] {title}*\n{message}\n_Time: {datetime.now().strftime('%H:%M:%S')}_"
            encoded_text = urllib.parse.quote(text)
            phone = self.callmebot_phone.replace("+", "").strip()
            url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_text}&apikey={self.callmebot_key}"
            
            req = urllib.request.Request(url, headers={"User-Agent": "NSEQuantEngine/1.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                pass
            logger.info("WhatsApp alert dispatched via CallMeBot")
        except Exception as e:
            logger.debug(f"WhatsApp (CallMeBot) dispatch failed: {e}")

    def _send_whatsapp_twilio(self, level: str, title: str, message: str):
        """Send WhatsApp message via Twilio API."""
        try:
            emoji = self._get_emoji(level)
            body = f"{emoji} *[{level}] {title}*\n{message}\n_Time: {datetime.now().strftime('%H:%M:%S')}_"
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            data = urllib.parse.urlencode({
                "From": self.twilio_from,
                "To": self.whatsapp_to,
                "Body": body
            }).encode("utf-8")
            
            import base64
            auth_header = "Basic " + base64.b64encode(f"{self.twilio_sid}:{self.twilio_token}".encode("utf-8")).decode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Authorization": auth_header}, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                pass
            logger.info("WhatsApp alert dispatched via Twilio")
        except Exception as e:
            logger.debug(f"WhatsApp (Twilio) dispatch failed: {e}")

    def _get_emoji(self, level: str) -> str:
        if level == "WARNING":
            return "⚠️"
        elif level in ["CRITICAL", "RISK"]:
            return "🚨"
        elif level == "TRADE":
            return "💹"
        return "ℹ️"

    # Specialized Alert Helpers
    def alert_trade_executed(self, portfolio_id: str, symbol: str, side: str, qty: int, price: float, stop: float, target: float, slippage: float):
        msg = f"Portfolio: {portfolio_id} | {side} {qty} shares of {symbol} @ ₹{price:.2f} (Slippage: ₹{slippage:.2f}) | SL: ₹{stop:.2f} | Tgt: ₹{target:.2f}"
        self.send_alert("TRADE", f"Trade Executed: {side} {symbol}", msg, {
            "portfolio": portfolio_id, "symbol": symbol, "side": side, "qty": qty, "price": price, "stop": stop, "target": target
        })

    def alert_exit_hit(self, portfolio_id: str, symbol: str, reason: str, pnl: float, exit_price: float):
        lvl = "TRADE" if pnl >= 0 else "WARNING"
        msg = f"Portfolio: {portfolio_id} | {symbol} exited due to {reason} @ ₹{exit_price:.2f}. Net PnL: ₹{pnl:+,.2f}"
        self.send_alert(lvl, f"Position Closed: {symbol} ({reason})", msg, {
            "portfolio": portfolio_id, "symbol": symbol, "reason": reason, "pnl": pnl, "exit_price": exit_price
        })

    def alert_risk_breach(self, rule_name: str, current_val: float, limit_val: float, action_taken: str):
        msg = f"Risk rule '{rule_name}' breached! Current: {current_val:.2f}%, Limit: {limit_val:.2f}%. Action: {action_taken}"
        self.send_alert("RISK", f"Risk Limit Breach: {rule_name}", msg, {
            "rule": rule_name, "current": current_val, "limit": limit_val, "action": action_taken
        })

    def alert_heartbeat_failure(self, worker_id: str, last_seen_minutes: float):
        msg = f"Worker {worker_id} heartbeat missed for {last_seen_minutes:.1f} minutes during NSE trading session."
        self.send_alert("CRITICAL", "Worker Heartbeat Failure", msg, {"worker_id": worker_id, "downtime_min": last_seen_minutes})


# Global singleton
alert_manager = AlertManager()
