import os
from typing import Any

import yaml

from pykis.client.auth import KisAuth
from pykis.kis import PyKis

__all__ = ["load_config", "create_client", "save_config_interactive"]


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    """Load YAML config from path."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_client(config_path: str = "config.yaml", keep_token: bool = True) -> PyKis:
    """Create a `PyKis` client from a YAML config file.

    If `virtual` is true in the config, the function will construct a
    `KisAuth` and pass it as the `virtual_auth` argument to `PyKis`.
    This avoids accidentally treating a virtual-only auth as a real auth.
    """
    cfg = load_config(config_path)

    auth = KisAuth(
        id=cfg["id"],
        appkey=cfg["appkey"],
        secretkey=cfg["secretkey"],
        account=cfg["account"],
        virtual=cfg.get("virtual", False),
    )

    if auth.virtual:
        # virtual-only credentials: pass as virtual_auth
        return PyKis(None, auth, keep_token=keep_token)

    return PyKis(auth, keep_token=keep_token)


def save_config_interactive(path: str = "config.yaml") -> dict[str, Any]:
    """Interactively prompt for config values and save to YAML.

    Returns the written dict.
    """
    data: dict[str, Any] = {}
    import os
    import getpass
    from typing import Any

    import yaml

    from pykis.client.auth import KisAuth
    from pykis.kis import PyKis

    __all__ = ["load_config", "create_client", "save_config_interactive"]


    def load_config(path: str = "config.yaml") -> dict[str, Any]:
        """Load YAML config from path."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


    def create_client(config_path: str = "config.yaml", keep_token: bool = True) -> PyKis:
        """Create a `PyKis` client from a YAML config file.

        If `virtual` is true in the config, the function will construct a
        `KisAuth` and pass it as the `virtual_auth` argument to `PyKis`.
        This avoids accidentally treating a virtual-only auth as a real auth.
        """
        cfg = load_config(config_path)

        auth = KisAuth(
            id=cfg["id"],
            appkey=cfg["appkey"],
            secretkey=cfg["secretkey"],
            account=cfg["account"],
            virtual=cfg.get("virtual", False),
        )

        if auth.virtual:
            # virtual-only credentials: pass as virtual_auth
            return PyKis(None, auth, keep_token=keep_token)

        return PyKis(auth, keep_token=keep_token)


    def save_config_interactive(path: str = "config.yaml") -> dict[str, Any]:
        """Interactively prompt for config values and save to YAML.

        This function hides the secret when echoing and asks for confirmation
        before writing. Set environment variable `PYKIS_CONFIRM_SKIP=1` to skip
        the interactive prompt (useful for CI scripts).

        Returns the written dict.
        """
        data: dict[str, Any] = {}
        data["id"] = input("HTS id: ")
        data["account"] = input("Account (XXXXXXXX-XX): ")
        data["appkey"] = input("AppKey: ")
        data["secretkey"] = getpass.getpass("SecretKey (input hidden): ")
        v = input("Virtual (y/n): ").strip().lower()
        data["virtual"] = v in ("y", "yes", "true", "1")

        # preview (masked secret)
        masked = (data["secretkey"][:4] + "...") if data.get("secretkey") else ""
        print("\nAbout to write the following config to: {}".format(path))
        print(f"  id: {data['id']}")
        print(f"  account: {data['account']}")
        print(f"  appkey: {data['appkey']}")
        print(f"  secretkey: {masked}")
        print(f"  virtual: {data['virtual']}\n")

        confirm = os.environ.get("PYKIS_CONFIRM_SKIP") == "1"
        if not confirm:
            ans = input("Write config file? (y/N): ").strip().lower()
            confirm = ans in ("y", "yes")

        if not confirm:
            raise SystemExit("Aborted by user")

        # write
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

        return data
