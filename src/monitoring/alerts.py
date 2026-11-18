"""
src/monitoring/alerts.py

Phase 14M: Resilient Multi-Channel Alerting System for NSE Autonomous Paper Trading.
Channels supported:
1. File append: reports/paper_trading/ALERTS.log
2. Telegram Bot (via TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
3. Generic Webhook (via ALERT_WEBHOOK_URL)
4. Structured Console Logger

All calls are non-blocking / fail-safe (wrapped in try/except) so alerting never crashes
the core trading engine.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("AlertManager")

class AlertManager:
    """Manages paper trading system alerts, warnings, and notifications."""

    def __init__(self, log_path: str = "reports/paper_trading/ALERTS.log"):
        self.log_path = log_path
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
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

        # 3. Webhook notification (if configured)
        if self.webhook_url:
            self._send_webhook(log_entry)

        # 4. Telegram notification (if configured)
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(level, title, message)

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
            emoji = "ℹ️"
            if level == "WARNING":
                emoji = "⚠️"
            elif level in ["CRITICAL", "RISK"]:
                emoji = "🚨"
            elif level == "TRADE":
                emoji = "💹"

            text = f"{emoji} *[{level}] {title}*\n{message}\n_Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = json.dumps({"chat_id": self.telegram_chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception as e:
            logger.debug(f"Telegram dispatch failed: {e}")

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
