from flask import Flask, request, jsonify, make_response
import requests
from datetime import datetime
import json
from xml.etree.ElementTree import Element, tostring, SubElement

# Protobuf helpers (use google.protobuf.struct_pb2 to serialize arbitrary JSON)
try:
    from google.protobuf import struct_pb2
    from google.protobuf import json_format
    HAS_PROTOBUF = True
except Exception:
    HAS_PROTOBUF = False

app = Flask(__name__)

# Armazenamento local (CRUD)
veiculos_local = []

# URL base da API externa (FIPE ou similar)
URL_API_EXTERNA = "https://parallelum.com.br/fipe/api/v1"   # você substitui aqui

def adicionar_veiculo_local(dados):
    for veiculo in veiculos_local:
        if veiculo["codigo_fipe"] == dados["codigo_fipe"]:
            return # já existe
    dados["id_local"] = len(veiculos_local) + 1
    dados["created_at"] = datetime.now().isoformat()
    dados["updated_at"] = datetime.now().isoformat()
    veiculos_local.append(dados)


# -------------------------------
# GET → Buscar da API externa
# -------------------------------
@app.get("/externo")
def buscar_externo():
    resposta = requests.get(f"{URL_API_EXTERNA}/carros/marcas")
    return respond(resposta.json())

@app.get("/externo/<marca>")
def buscar_externo_marca(marca):
    resposta = requests.get(f"{URL_API_EXTERNA}/carros/marcas/{marca}/modelos")
    return respond(resposta.json())

@app.get("/externo/<marca>/<modelo>")
def buscar_externo_modelo(marca, modelo):
    resposta = requests.get(f"{URL_API_EXTERNA}/carros/marcas/{marca}/modelos/{modelo}/anos")
    return respond(resposta.json())

@app.get("/externo/<marca>/<modelo>/<ano>")
def buscar_externo_ano(marca, modelo, ano):
    resposta = requests.get(f"{URL_API_EXTERNA}/carros/marcas/{marca}/modelos/{modelo}/anos/{ano}")
    adicionar_veiculo_local(resposta.json())
    return respond(resposta.json())

# -------------------------------
# CRUD LOCAL
# -------------------------------

@app.get("/veiculos")
def listar_veiculos():
    return respond(veiculos_local)


@app.post("/veiculos")
def criar_veiculo():
    dados = request.json
    for v in veiculos_local:
        if v["codigo_fipe"] == dados["codigo_fipe"]:
            return jsonify({"erro": "Veículo já existe"}), 400
    dados["id_local"] = len(veiculos_local) + 1
    dados["created_at"] = datetime.now().isoformat()
    dados["updated_at"] = datetime.now().isoformat()
    veiculos_local.append(dados)
    return respond(dados, status=201)


@app.get("/veiculos/<int:id_local>")
def obter_veiculo(id_local):
    for v in veiculos_local:
        if v["id_local"] == id_local:
            return respond(v)
    return jsonify({"erro": "Não encontrado"}), 404


@app.put("/veiculos/<int:id_local>")
def atualizar_veiculo(id_local):
    for v in veiculos_local:
        if v["id_local"] == id_local:
            novo = request.json
            v.update(novo)
            v["updated_at"] = datetime.now().isoformat()
            return respond(v)
    return jsonify({"erro": "Não encontrado"}), 404


@app.delete("/veiculos/<int:id_local>")
def deletar_veiculo(id_local):
    for v in veiculos_local:
        if v["id_local"] == id_local:
            veiculos_local.remove(v)
            return respond(None, status=204)
    return jsonify({"erro": "Não encontrado"}), 404


# -------------------------------
# Content negotiation helpers
# -------------------------------
def get_requested_format():
    # priority: ?format= over Accept header
    fmt = None
    q = request.args.get('format')
    if q:
        q = q.lower()
        if q in ('json', 'xml', 'protobuf'):
            return q
    accept = request.headers.get('Accept', '')
    if 'application/x-protobuf' in accept or 'application/octet-stream' in accept or 'application/protobuf' in accept:
        return 'protobuf'
    if 'application/xml' in accept or 'text/xml' in accept:
        return 'xml'
    return 'json'


def dict_to_xml(data, root_name='response'):
    def build(elem, val):
        if isinstance(val, dict):
            for k, v in val.items():
                # sanitize tag name slightly
                tag = str(k)
                child = SubElement(elem, tag)
                build(child, v)
        elif isinstance(val, list):
            for item in val:
                item_elem = SubElement(elem, 'item')
                build(item_elem, item)
        elif val is None:
            elem.text = ''
        else:
            elem.text = str(val)

    root = Element(root_name)
    build(root, data)
    xml_bytes = tostring(root, encoding='utf-8')
    return '<?xml version="1.0" encoding="utf-8"?>' + xml_bytes.decode('utf-8')


def serialize(data, fmt):
    if fmt == 'json':
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return body, 'application/json; charset=utf-8'
    if fmt == 'xml':
        body = dict_to_xml(data if data is not None else {})
        return body.encode('utf-8'), 'application/xml; charset=utf-8'
    if fmt == 'protobuf':
        if not HAS_PROTOBUF:
            return json.dumps({'erro': 'Protobuf não disponível no servidor'}).encode('utf-8'), 'application/json; charset=utf-8'
        # pack arbitrary JSON into google.protobuf.Struct
        s = struct_pb2.Struct()
        # json_format.ParseDict works for mapping dict -> Struct
        json_format.ParseDict(data if data is not None else {}, s)
        return s.SerializeToString(), 'application/x-protobuf'
    # fallback
    return json.dumps(data, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8'


def respond(data, status=200):
    # If no content (e.g., delete with 204)
    if data is None and status == 204:
        return '', 204
    fmt = get_requested_format()
    body, content_type = serialize(data, fmt)
    resp = make_response(body, status)
    resp.headers['Content-Type'] = content_type
    return resp


if __name__ == "__main__":
    app.run(debug=True)