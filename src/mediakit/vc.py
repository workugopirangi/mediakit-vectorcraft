"""Cliente do VectorCraft sem tela (vectorcraft-cli mcp --headless), um processo por chamador.
Uso: v = VC(); v.ex("shape.rectangle", {...}); v.close()"""
import json
import subprocess
from pathlib import Path

from mediakit import config


class VCError(Exception):
    pass


def versao_travada():
    return config.VERSAO_VC.read_text().strip()


def versao_instalada(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def conferir_versao(repo=None):
    repo = Path(repo or config.VC_REPO)
    tem, quer = versao_instalada(repo), versao_travada()
    if tem != quer:
        raise VCError(f"VectorCraft em {repo} está no commit {tem[:10]}, mas o testado é {quer[:10]}. "
                      f"Rode scripts/montar_vectorcraft.sh para voltar à versão testada.")


class VC:
    def __init__(self, read_root="/", write_root="/"):
        self.p = subprocess.Popen([str(config.VC_CLI), "mcp", "--headless", "--automation-read-root", read_root,
                                   "--automation-write-root", write_root],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, bufsize=1)
        self.n = 0
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "mediakit", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise VCError("vectorcraft-cli encerrou")
            m = json.loads(line)
            if m.get("id") == self.n:
                if "error" in m:
                    raise VCError(f"{method}: {m['error']}")
                return m["result"]

    def tool(self, name, args):
        r = self._rpc("tools/call", {"name": name, "arguments": args})
        txt = "".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        if r.get("isError"):
            raise VCError(f"{name} {json.dumps(args, ensure_ascii=False)[:200]} -> {txt[:400]}")
        try:
            return json.loads(txt)
        except ValueError:
            return txt

    def ex(self, command, params=None):
        return self.tool("run_command", {"command": command, "params": params or {}})

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
