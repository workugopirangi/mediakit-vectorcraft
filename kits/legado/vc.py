import socket,json
_n=[0]
class VCError(Exception): pass
def call(method,params=None,t=120):
    _n[0]+=1
    s=socket.create_connection(("127.0.0.1",7981),timeout=t)
    s.sendall((json.dumps({"id":_n[0],"method":method,"params":params or {}})+"\n").encode())
    buf=b""
    while not buf.endswith(b"\n"):
        c=s.recv(1<<20)
        if not c: break
        buf+=c
    s.close()
    return json.loads(buf)
def ex(cmd,params=None,t=120):
    r=call("engine.execute",{"command":cmd,"params":params or {}},t)
    if not r.get("ok"): raise VCError(f"{cmd} {json.dumps(params,ensure_ascii=False)[:200]} -> {r.get('error')}")
    return r.get("result")


def close_all_discard():
    """Fecha todos os documentos sem salvar (o que importa já foi exportado e salvo antes)."""
    for _ in range(10):
        r = call("engine.execute", {"command": "file.closeAll", "params": {}})
        pend = (r.get("result") or {}).get("pending") if r.get("ok") else None
        if not pend:
            return
        call("ui.dialog.set", {"field": "discard", "value": True})
        call("ui.dialog.confirm", {})
