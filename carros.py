import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests

# Configuração da API
BASE_URL = "http://127.0.0.1:5000"

class VeiculosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente Desktop - Gestão de Veículos REST")
        self.root.geometry("1200x900")

        # Variáveis de dados
        self.marcas_data = []
        self.modelos_data = []
        self.anos_data = []

        # --- Layout Principal ---
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === LADO ESQUERDO: Integração FIPE ===
        left_frame = tk.LabelFrame(main_frame, text="1. Buscar na FIPE (Adicionar)", padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Dropdowns
        tk.Label(left_frame, text="Marca:").pack(anchor=tk.W)
        self.combo_marca = ttk.Combobox(left_frame, state="readonly")
        self.combo_marca.pack(fill=tk.X, pady=(0, 10))
        self.combo_marca.bind("<<ComboboxSelected>>", self.ao_selecionar_marca)

        tk.Label(left_frame, text="Modelo:").pack(anchor=tk.W)
        self.combo_modelo = ttk.Combobox(left_frame, state="readonly")
        self.combo_modelo.pack(fill=tk.X, pady=(0, 10))
        self.combo_modelo.bind("<<ComboboxSelected>>", self.ao_selecionar_modelo)

        tk.Label(left_frame, text="Ano:").pack(anchor=tk.W)
        self.combo_ano = ttk.Combobox(left_frame, state="readonly")
        self.combo_ano.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_salvar = tk.Button(left_frame, text="💾 Buscar e Salvar no Servidor", 
                                    bg="#4CAF50", fg="white", command=self.salvar_veiculo)
        self.btn_salvar.pack(fill=tk.X, pady=20)

        # === LADO DIREITO: Lista Local ===
        right_frame = tk.LabelFrame(main_frame, text="2. Veículos Locais (Ranking)", padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Tabela
        cols = ("ID", "Modelo", "Ano", "Votos")
        self.tree = ttk.Treeview(right_frame, columns=cols, show="headings", height=15)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Modelo", text="Modelo")
        self.tree.heading("Ano", text="Ano")
        self.tree.heading("Votos", text="Votos")
        
        self.tree.column("ID", width=40)
        self.tree.column("Modelo", width=200)
        self.tree.column("Ano", width=80)
        self.tree.column("Votos", width=60)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Botões de Ação
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="🔄 Atualizar", command=self.atualizar_lista).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="👍 Like (+1)", command=self.votar_like, bg="#e6ffe6").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="✏️ Editar", command=self.abrir_edicao, bg="#fffec8").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Deletar", command=self.deletar, bg="#ffcccc").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="📄 XML", command=self.ver_xml_raw, bg="#e0f7fa").pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="🧾 JSON", command=self.ver_json_raw, bg="#eeeeff").pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="📦 Proto", command=self.ver_proto_raw, bg="#f0f0f0").pack(side=tk.RIGHT, padx=2)


        # Início
        self.carregar_marcas()
        self.atualizar_lista()

    # --- Métodos API FIPE ---
    def carregar_marcas(self):
        try:
            resp = requests.get(f"{BASE_URL}/externo", timeout=5)
            resp.raise_for_status()
            self.marcas_data = resp.json()
            # Garante que temos uma lista de nomes (defensivo)
            self.combo_marca['values'] = [m.get('nome', '') for m in self.marcas_data]
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao conectar (marcas): {e}")

    def ao_selecionar_marca(self, event):
        try:
            idx = self.combo_marca.current()
            if idx < 0: return
            cod_marca = self.marcas_data[idx]['codigo']
            self.combo_modelo.set(''); self.combo_ano.set('')
            
            resp = requests.get(f"{BASE_URL}/externo/{cod_marca}", timeout=5)
            resp.raise_for_status()
            self.modelos_data = resp.json().get('modelos', [])
            self.combo_modelo['values'] = [m.get('nome', '') for m in self.modelos_data]
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar modelos: {e}")

    def ao_selecionar_modelo(self, event):
        try:
            idx_marca = self.combo_marca.current()
            idx_modelo = self.combo_modelo.current()
            if idx_marca < 0 or idx_modelo < 0: return
            cod_marca = self.marcas_data[idx_marca]['codigo']
            cod_modelo = self.modelos_data[idx_modelo]['codigo']
            
            resp = requests.get(f"{BASE_URL}/externo/{cod_marca}/{cod_modelo}", timeout=5)
            resp.raise_for_status()
            self.anos_data = resp.json()
            self.combo_ano['values'] = [a.get('nome', '') for a in self.anos_data]
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar anos: {e}")

    def salvar_veiculo(self):
        if self.combo_ano.get() == "":
            messagebox.showwarning("Atenção", "Selecione o ano.")
            return
        try:
            cod_marca = self.marcas_data[self.combo_marca.current()]['codigo']
            cod_modelo = self.modelos_data[self.combo_modelo.current()]['codigo']
            cod_ano = self.anos_data[self.combo_ano.current()]['codigo']
            resp = requests.get(f"{BASE_URL}/externo/{cod_marca}/{cod_modelo}/{cod_ano}", timeout=5)
            resp.raise_for_status()
            self.atualizar_lista()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar veículo: {e}")

    # --- Métodos CRUD Local ---
    def atualizar_lista(self):
        # Limpa e recarrega
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            resp = requests.get(f"{BASE_URL}/veiculos/ranking", timeout=5)
            resp.raise_for_status()
            dados = resp.json()
            for v in dados:
                # defensivo: usa get com fallback
                id_local = v.get('id_local') or v.get('id') or ''
                modelo = v.get('Modelo', '')
                ano = v.get('AnoModelo', '')
                votos = v.get('votos', 0)
                self.tree.insert("", "end", values=(id_local, modelo, ano, votos))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar lista: {e}")

    def obter_dados_selecionados(self):
        selected = self.tree.focus()
        if not selected:
            return None, None
        item = self.tree.item(selected)
        vals = item.get('values', [])
        if not vals:
            return None, None
        return vals[0], vals

    def votar_like(self):
        id_local, _ = self.obter_dados_selecionados()
        if not id_local:
            messagebox.showwarning("Aviso", "Selecione um veículo.")
            return
        try:
            requests.post(f"{BASE_URL}/veiculos/{id_local}/votar", timeout=5)
            self.atualizar_lista()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao votar: {e}")


    # --- LÓGICA DE EDIÇÃO ---
    def abrir_edicao(self):
        id_local, values = self.obter_dados_selecionados()
        if not id_local:
            messagebox.showwarning("Aviso", "Selecione um veículo para editar.")
            return

        top = tk.Toplevel(self.root)
        top.title(f"Editar Veículo ID {id_local}")
        top.geometry("320x220")
        top.resizable(False, False)

        tk.Label(top, text="Modelo:").pack(pady=(10, 0))
        entry_modelo = tk.Entry(top, width=40)
        entry_modelo.insert(0, values[1])
        entry_modelo.pack(pady=5)

        tk.Label(top, text="Ano:").pack(pady=(10, 0))
        entry_ano = tk.Entry(top, width=40)
        entry_ano.insert(0, str(values[2]))
        entry_ano.pack(pady=5)

        # Botão salvar chama a função que fecha a janela
        btn_confirmar = tk.Button(top, text="Salvar Alterações", bg="#4CAF50", fg="white",
                                  command=lambda: self.enviar_edicao(id_local, entry_modelo.get(), entry_ano.get(), top))
        btn_confirmar.pack(pady=15)

    def enviar_edicao(self, id_local, novo_modelo, novo_ano, window):
        # Envia o payload com os campos que o backend espera (Modelo, AnoModelo)
        dados = {"Modelo": novo_modelo, "AnoModelo": novo_ano}
        try:
            resp = requests.put(f"{BASE_URL}/veiculos/{id_local}", json=dados, headers={"Content-Type": "application/json"}, timeout=5)
            if resp.status_code in (200, 204):
                self.atualizar_lista()
                window.destroy()
                messagebox.showinfo("Sucesso", "Veículo atualizado com sucesso.")
            else:
                # tenta pegar mensagem de erro do servidor
                try:
                    msg = resp.json().get('detail') if resp.headers.get('Content-Type','').startswith('application/json') else resp.text
                except:
                    msg = resp.text
                messagebox.showerror("Erro", f"Falha ao atualizar (status {resp.status_code}): {msg}")
        except Exception as e:
            messagebox.showerror("Erro", f"Conexão: {e}")

    def deletar(self):
        id_local, _ = self.obter_dados_selecionados()
        if not id_local:
            messagebox.showwarning("Aviso", "Selecione um veículo.")
            return
        if messagebox.askyesno("Confirmar", "Deletar este veículo?"):
            try:
                requests.delete(f"{BASE_URL}/veiculos/{id_local}", timeout=5)
                self.atualizar_lista()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao deletar: {e}")

    def ver_xml_raw(self):
        id_local, _ = self.obter_dados_selecionados()
        if not id_local:
            messagebox.showwarning("Aviso", "Selecione um veículo.")
            return
        try:
            headers = {'Accept': 'application/xml'}
            resp = requests.get(f"{BASE_URL}/veiculos/{id_local}", headers=headers, timeout=5)
            top = tk.Toplevel(self.root)
            top.title(f"XML - Veículo {id_local}")
            txt = scrolledtext.ScrolledText(top, width=80, height=30)
            txt.pack(padx=10, pady=10)
            txt.insert(tk.INSERT, resp.text)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao buscar XML: {e}")

    def ver_json_raw(self):
        id_local, _ = self.obter_dados_selecionados()
        if not id_local:
            messagebox.showwarning("Aviso", "Selecione um veículo.")
            return
        try:
            headers = {'Accept': 'application/json'}
            resp = requests.get(f"{BASE_URL}/veiculos/{id_local}", headers=headers, timeout=5)

            top = tk.Toplevel(self.root)
            top.title(f"JSON - Veículo {id_local}")

            txt = scrolledtext.ScrolledText(top, width=80, height=30)
            txt.pack(padx=10, pady=10)

            # Formata bonito igual ao navegador
            txt.insert(tk.INSERT, resp.json())

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao buscar JSON: {e}")


    def ver_proto_raw(self):
        id_local, _ = self.obter_dados_selecionados()
        if not id_local:
            messagebox.showwarning("Aviso", "Selecione um veículo.")
            return
        try:
            headers = {'Accept': 'application/x-protobuf'}
            resp = requests.get(f"{BASE_URL}/veiculos/{id_local}", headers=headers, timeout=5)

            top = tk.Toplevel(self.root)
            top.title(f"ProtoBuf - Veículo {id_local}")

            txt = scrolledtext.ScrolledText(top, width=80, height=30)
            txt.pack(padx=10, pady=10)

            # Exibe os bytes em hexadecimal
            hex_dump = resp.content.hex(" ")
            txt.insert(tk.INSERT, hex_dump)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao buscar ProtoBuf: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VeiculosApp(root)
    root.mainloop()
