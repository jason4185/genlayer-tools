# { "Depends": "py-genlayer:test" }

from genlayer import *
import json
import typing


def is_valid_address(address: str) -> bool:
    if not address:
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    valid_chars = "0123456789abcdefABCDEF"
    for char in address[2:]:
        if char not in valid_chars:
            return False
    return True


class SecureAPIGateway(gl.Contract):

    api_key:         str
    owner:           str   # wallet address of the contract deployer
    last_response:   str
    allowed_callers: str
    audit_log:       str
    call_count:      str
    rate_limit:      str
    is_paused:       str
    key_version:     str

    def __init__(self, api_key: str, owner_address: str):   # owner address passed at deploy time
        assert is_valid_address(owner_address), "Invalid owner address. Must start with 0x and be 42 characters long."
        self.api_key         = api_key
        self.owner           = owner_address               # store owner address
        self.last_response   = ""
        self.allowed_callers = json.dumps([owner_address]) # owner is auto-whitelisted
        self.audit_log       = json.dumps([])
        self.call_count      = "0"
        self.rate_limit      = "100"
        self.is_paused       = "false"
        self.key_version     = "1"

    def _is_owner(self, address: str) -> bool:             # check if address is the owner
        return address == self.owner

    def _log_call(self, url: str, status: str) -> None:
        log   = json.loads(self.audit_log)
        entry = {
            "call_number": self.call_count,
            "url":         url,
            "status":      status,
            "key_version": self.key_version,
        }
        log.append(entry)
        if len(log) > 50:
            log = log[-50:]
        self.audit_log = json.dumps(log)

    # ── OWNER ONLY METHODS ─────────────────────────────────────────

    @gl.public.write
    def add_allowed_caller(self, caller_address: str, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can add callers."
        assert is_valid_address(caller_address), "Invalid wallet address: " + caller_address + ". Must start with 0x and be 42 characters long."
        callers = json.loads(self.allowed_callers)
        assert caller_address not in callers, "Address " + caller_address + " is already in the whitelist."
        callers.append(caller_address)
        self.allowed_callers = json.dumps(callers)

    @gl.public.write
    def bulk_add_callers(self, addresses: list, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can add callers."
        callers = json.loads(self.allowed_callers)
        added   = []
        skipped = []
        invalid = []
        for address in addresses:
            if not is_valid_address(address):
                invalid.append(address)
                continue
            if address in callers:
                skipped.append(address)
                continue
            callers.append(address)
            added.append(address)
        self.allowed_callers = json.dumps(callers)
        log = json.loads(self.audit_log)
        log.append({
            "bulk_add": {
                "added":   added,
                "skipped": skipped,
                "invalid": invalid,
                "message": str(len(added)) + " added, " + str(len(skipped)) + " skipped, " + str(len(invalid)) + " invalid."
            }
        })
        self.audit_log = json.dumps(log)

    @gl.public.write
    def remove_allowed_caller(self, caller_address: str, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can remove callers."
        callers = json.loads(self.allowed_callers)
        log     = json.loads(self.audit_log)

        if not is_valid_address(caller_address):
            log.append({"remove_attempt": caller_address, "status": "rejected", "reason": "Invalid address format."})
            self.audit_log = json.dumps(log)
            return

        if caller_address not in callers:
            log.append({"remove_attempt": caller_address, "status": "rejected", "reason": "Address not in whitelist."})
            self.audit_log = json.dumps(log)
            return

        callers.remove(caller_address)
        self.allowed_callers = json.dumps(callers)
        log.append({"remove_attempt": caller_address, "status": "removed", "reason": "Address successfully removed."})
        self.audit_log = json.dumps(log)

    @gl.public.write
    def rotate_key(self, new_key: str, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can rotate the key."
        assert len(new_key) >= 8, "Invalid API key. Key must be at least 8 characters long."
        self.api_key     = new_key
        self.key_version = str(int(self.key_version) + 1)
        self._log_call("KEY_ROTATION", "key_rotated")

    @gl.public.write
    def set_rate_limit(self, limit: str, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can set the rate limit."
        assert limit.isdigit(), "Invalid rate limit: " + limit + ". Must be a whole number e.g. 100."
        assert int(limit) >= 1, "Rate limit must be at least 1."
        self.rate_limit = limit

    @gl.public.write
    def reset_call_count(self, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can reset the call count."
        self.call_count = "0"
        self._log_call("RESET", "call_count_reset")

    @gl.public.write
    def pause(self, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can pause the contract."
        assert self.is_paused == "false", "Contract is already paused."
        self.is_paused = "true"

    @gl.public.write
    def unpause(self, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the contract owner can unpause the contract."
        assert self.is_paused == "true", "Contract is not paused."
        self.is_paused = "false"

    @gl.public.write
    def transfer_ownership(self, new_owner: str, owner_address: str) -> typing.Any:
        assert self._is_owner(owner_address), "Access denied. Only the current owner can transfer ownership."
        assert is_valid_address(new_owner), "Invalid new owner address: " + new_owner + ". Must start with 0x and be 42 characters long."
        assert new_owner != self.owner, "New owner address is the same as the current owner."
        old_owner  = self.owner
        self.owner = new_owner
        log = json.loads(self.audit_log)
        log.append({"ownership_transfer": {"from": old_owner, "to": new_owner, "status": "completed"}})
        self.audit_log = json.dumps(log)

    # ── FETCH METHODS ──────────────────────────────────────────────

    @gl.public.write
    def fetch_with_key(self, url: str) -> typing.Any:
        assert self.is_paused == "false", "Contract is paused. Contact the owner to unpause."  # single pause check
        assert url.startswith("http"), "Invalid URL. Must start with http:// or https://"
        count = int(self.call_count)
        limit = int(self.rate_limit)
        if count >= limit:
            self.last_response = json.dumps({
                "error":  "Rate limit reached (" + self.rate_limit + " calls). Contact the owner to increase the limit.",
                "status": "rate_limited"
            })
            return
        api_key = self.api_key

        def fetch() -> str:
            try:
                raw = gl.nondet.web.render(url + api_key, mode="text")
                if not raw or raw.strip() == "null":
                    return json.dumps({"error": "API is down or returned empty response.", "status": "unavailable"})
                data = json.loads(raw)
                return json.dumps({"status": "ok", "response": data})
            except Exception:
                return json.dumps({"error": "API call failed. Check your URL and try again.", "status": "error"})

        fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same API response. They are equivalent if both show the same error status or the response data matches.")
        self.last_response = fresh
        self.call_count    = str(count + 1)
        self._log_call(url, "success")

    @gl.public.write
    def fetch_with_key_param(self, url: str, param_name: str) -> typing.Any:
        assert self.is_paused == "false", "Contract is paused. Contact the owner to unpause."  # single pause check
        assert url.startswith("http"), "Invalid URL. Must start with http:// or https://"
        assert len(param_name) > 0, "Invalid parameter name. Provide the API key parameter name e.g. appid."
        count   = int(self.call_count)
        limit   = int(self.rate_limit)
        if count >= limit:
            self.last_response = json.dumps({
                "error":  "Rate limit reached (" + self.rate_limit + " calls). Contact the owner to increase the limit.",
                "status": "rate_limited"
            })
            return
        api_key = self.api_key
        param   = param_name

        def fetch() -> str:
            try:
                raw = gl.nondet.web.render(url + param + "=" + api_key, mode="text")
                if not raw or raw.strip() == "null":
                    return json.dumps({"error": "API is down or returned empty response.", "status": "unavailable"})
                data = json.loads(raw)
                return json.dumps({"status": "ok", "response": data})
            except Exception:
                return json.dumps({"error": "API call failed. Check your URL and parameter name.", "status": "error"})

        fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same API response. They are equivalent if both show the same error status or the response data matches.")
        self.last_response = fresh
        self.call_count    = str(count + 1)
        self._log_call(url, "success")

    # ── FREE READ METHODS ──────────────────────────────────────────

    @gl.public.view
    def get_security_status(self) -> str:
        callers = json.loads(self.allowed_callers)
        return json.dumps({
            "owner":           self.owner,
            "is_paused":       self.is_paused,
            "key_version":     self.key_version,
            "api_key_stored":  "yes",
            "api_key_exposed": "no",
            "total_callers":   str(len(callers)),
            "allowed_callers": callers,
            "calls_made":      self.call_count,
            "rate_limit":      self.rate_limit,
            "calls_remaining": str(int(self.rate_limit) - int(self.call_count)),
        })

    @gl.public.view
    def get_whitelist(self) -> str:
        callers = json.loads(self.allowed_callers)
        return json.dumps({"total": str(len(callers)), "callers": callers})

    @gl.public.view
    def get_caller_count(self) -> str:
        callers = json.loads(self.allowed_callers)
        return json.dumps({"count": str(len(callers))})

    @gl.public.view
    def is_caller_allowed(self, address: str) -> str:
        if not is_valid_address(address):
            return json.dumps({"error": "Invalid wallet address format.", "address": address, "allowed": False})
        callers = json.loads(self.allowed_callers)
        return json.dumps({"address": address, "allowed": address in callers})

    @gl.public.view
    def get_call_count(self) -> str:
        return json.dumps({
            "calls_made":      self.call_count,
            "rate_limit":      self.rate_limit,
            "calls_remaining": str(int(self.rate_limit) - int(self.call_count)),
        })

    @gl.public.view
    def get_remaining_calls(self) -> str:
        remaining = int(self.rate_limit) - int(self.call_count)
        return json.dumps({
            "remaining": str(remaining),
            "message":   str(remaining) + " calls remaining out of " + self.rate_limit,
        })

    @gl.public.view
    def is_paused_status(self) -> str:
        return json.dumps({
            "paused":  self.is_paused,
            "message": "Contract is paused." if self.is_paused == "true" else "Contract is active.",
        })

    @gl.public.view
    def get_key_version(self) -> str:
        return json.dumps({
            "version": self.key_version,
            "message": "Key has been rotated " + str(int(self.key_version) - 1) + " time(s).",
        })

    @gl.public.view
    def get_owner(self) -> str:
        return json.dumps({"owner": self.owner})

    @gl.public.view
    def get_last_response(self) -> str:
        if not self.last_response:
            return json.dumps({
                "message": "No API calls made yet.",
                "hint":    "Call fetch_with_key or fetch_with_key_param to make your first secure API call."
            })
        return self.last_response

    @gl.public.view
    def get_audit_log(self) -> str:
        return self.audit_log