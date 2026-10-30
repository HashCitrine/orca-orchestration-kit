#!/usr/bin/env python3
"""Small official Jev client; credentials and request bodies are never logged."""

import argparse
import getpass
import json
import os
from pathlib import Path
import socket
import stat
import sys
import tempfile
import urllib.error
import urllib.request

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
CREDENTIALS = Path.home() / ".config/jev/credentials.json"


class JevError(Exception):
    pass


def credential():
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key, "environment"
    if os.name == "nt":
        raise JevError("missing_key: set TYPESAFE_API_KEY in your environment on Windows")
    try:
        fd = os.open(CREDENTIALS, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        raise JevError("missing_key: run configure in your own terminal") from None
    except OSError:
        raise JevError("credential_file: cannot securely open credentials") from None
    with os.fdopen(fd, "r", encoding="utf-8") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise JevError("credential_permissions: require owned regular file with mode 0600")
        try:
            data = json.load(stream)
        except (ValueError, UnicodeError):
            raise JevError("credential_file: invalid JSON") from None
    key = data.get("api_key") if isinstance(data, dict) else None
    if not isinstance(key, str) or not key.strip():
        raise JevError("credential_file: nonempty api_key required")
    return key.strip(), "credential_file"


def configure():
    if os.name == "nt":
        raise JevError("use TYPESAFE_API_KEY on Windows; credential file ACL setup is not supported")
    if not sys.stdin.isatty():
        raise JevError("interactive_terminal_required: run configure in your own terminal")
    if CREDENTIALS.exists() or CREDENTIALS.is_symlink():
        raise JevError("credential_exists: existing credentials were not overwritten")
    key = getpass.getpass("TypeSafe API key (hidden): ").strip()
    if not key or any(ch.isspace() for ch in key):
        raise JevError("invalid_key: expected a nonempty key without whitespace")
    CREDENTIALS.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".credentials-", dir=CREDENTIALS.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"api_key": key}, stream)
            stream.write("\n")
        # Atomic publication without overwriting an existing credential.
        os.link(temporary, CREDENTIALS)
    finally:
        os.unlink(temporary)
    print("Credentials saved with mode 0600; key not displayed.")


def validate_request(payload):
    if not isinstance(payload, dict):
        raise JevError("invalid_input: expected a JSON object")
    if set(payload) - {"state", "questions", "model"}:
        raise JevError("invalid_input: supported fields are state, questions, model")
    if not isinstance(payload.get("state"), (str, dict, list)):
        raise JevError("invalid_input: state must be a string, object, or array")
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise JevError("invalid_input: questions must be a nonempty object")
    for question in questions.values():
        if not isinstance(question, dict) or question.get("type") not in {"choice", "score", "noul"}:
            raise JevError("invalid_input: expected choice, score, or noul question")
        if not isinstance(question.get("instructions"), (str, dict, list)):
            raise JevError("invalid_input: question instructions required")
        criteria = question.get("criteria")
        if question["type"] == "choice" and (not isinstance(criteria, dict) or not 1 <= len(criteria) <= 255):
            raise JevError("invalid_input: Choice requires 1 to 255 criteria")
        if question["type"] == "score" and (not isinstance(criteria, list) or not 2 <= len(criteria) <= 10):
            raise JevError("invalid_input: Score requires 2 to 10 criteria")
    payload.setdefault("model", "jev-latest")
    if not isinstance(payload["model"], str) or not payload["model"].strip():
        raise JevError("invalid_input: model must be a nonempty string")
    return payload


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def evaluate(payload):
    payload = validate_request(payload)
    key, _ = credential()
    try:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        request = urllib.request.Request(ENDPOINT, data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json",
        }, method="POST")
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        category = {401: "authentication_failed", 403: "access_denied", 429: "rate_limited"}.get(error.code, "api_error")
        raise JevError(f"{category}: HTTP {error.code}; no automatic retry") from None
    except (socket.timeout, TimeoutError):
        raise JevError("timeout: 30-second limit; no automatic retry") from None
    except (urllib.error.URLError, OSError):
        raise JevError("connection_failed: check connectivity; no automatic retry") from None
    except (ValueError, UnicodeError):
        raise JevError("invalid_data: request or response could not be encoded or decoded") from None
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
        raise JevError("invalid_response: expected answers object")
    if set(result["answers"]) != set(payload["questions"]):
        raise JevError("invalid_response: answer IDs differ from requested questions")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("configure", help="Save a key through hidden terminal input")
    sub.add_parser("status", help="Check credential presence without displaying it")
    run = sub.add_parser("evaluate", help="Evaluate JSON from stdin or a file")
    run.add_argument("--input", default="-")
    args = parser.parse_args()
    try:
        if args.command == "configure":
            configure()
        elif args.command == "status":
            _, source = credential()
            print(json.dumps({"configured": True, "source": source}))
        else:
            if args.input == "-":
                payload = json.load(sys.stdin)
            else:
                with open(args.input, encoding="utf-8") as stream:
                    payload = json.load(stream)
            print(json.dumps(evaluate(payload), ensure_ascii=False, allow_nan=False))
    except JevError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, UnicodeError):
        print("local_error: check input file, JSON, and file permissions", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("cancelled: no request retry", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
