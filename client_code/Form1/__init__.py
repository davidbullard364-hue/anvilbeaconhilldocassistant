from ._anvil_designer import Form1Template
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil
import anvil.media
import anvil.server


class Form1(Form1Template):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.clear()
        self.background = "#faf6ed"
        self.history = []
        self.last_question = None
        self.summary_history = []
        self.summary_title = None

        self.add_component(anvil.Label(
            text="Beacon Hill Document Assistant", font_size=30,
            bold=True, foreground="#355344",
        ))
        self.add_component(anvil.Label(text="A resident-maintained resource for community documents."))
        nav = anvil.FlowPanel()
        self.add_component(nav)
        for name, handler in [
            ("Welcome", self.welcome), ("Document Assistant", self.chat),
            ("Executive Summaries", self.summaries), ("Owner tools", self.owner),
        ]:
            self.button(nav, name, handler)

        self.panel = anvil.ColumnPanel(background="#fffdf8")
        self.add_component(self.panel)
        self.welcome()

    def button(self, panel, title, handler, primary=False):
        button = anvil.Button(text=title)
        button.background = "#355344" if primary else "#efede8"
        button.foreground = "#ffffff" if primary else "#292b24"
        button.set_event_handler("click", handler)
        panel.add_component(button)
        return button

    def welcome(self, **event):
        self.panel.clear()
        self.panel.add_component(anvil.RichText(format="markdown", content=(
            "## Welcome\n\n"
            "**Document Assistant** searches the community collection and answers questions with "
            "document and page citations. Try a starter question or ask one of your own.\n\n"
            "**Executive Summaries** gives you a plain-language overview of a selected document. "
            "Ask follow-up questions about the same document after reading its summary."
        )))

    def show_answer(self, panel, question, result):
        panel.add_component(anvil.Label(text=question, bold=True))
        panel.add_component(anvil.RichText(format="markdown", content=result["text"]))
        for source in result["sources"]:
            title = source["title"]
            self.button(panel, "[{}] {} · PDF page {}".format(
                source["number"], title, source["page"],
            ), lambda title=title, **event: self.open_pdf(title))

    def open_pdf(self, title):
        media = anvil.server.call("get_pdf", title)
        if media:
            anvil.media.download(media)
        else:
            anvil.alert("The original PDF is unavailable. This document was imported as indexed text.")

    def chat(self, **event):
        self.panel.clear()
        question = anvil.TextArea(placeholder="Ask about Beacon Hill documents")
        self.panel.add_component(question)
        controls = anvil.FlowPanel()
        self.panel.add_component(controls)
        conversation = anvil.ColumnPanel()
        self.panel.add_component(conversation)

        def render():
            conversation.clear()
            for prompt, result in self.history:
                self.show_answer(conversation, prompt, result)

        def ask(prompt):
            if not prompt.strip():
                anvil.alert("Enter a question first.")
                return
            self.last_question = prompt
            history = [turn for q, result in self.history[-4:] for turn in (
                {"role": "user", "content": q}, {"role": "assistant", "content": result["text"]},
            )]
            result = anvil.server.call("answer", prompt, history)
            if "error" in result:
                anvil.alert(result["error"])
                return
            self.history.append((prompt, result))
            question.text = ""
            render()

        def reset(**event):
            self.history.clear()
            self.last_question = None
            render()

        self.button(controls, "Ask", lambda **e: ask(question.text or ""), primary=True)
        self.button(controls, "Retry last question", lambda **e: ask(self.last_question or ""))
        self.button(controls, "New conversation", reset)
        starters = anvil.FlowPanel()
        self.panel.add_component(starters, index=2)
        for prompt in (
            "How do I file a complaint?", "Summarize the bylaws",
            "What records does the association retain?", "Explain the conflict-of-interest policy",
        ):
            self.button(starters, prompt, lambda prompt=prompt, **e: ask(prompt))
        for prompt in ("Explain the previous answer more simply.", "Show the supporting wording."):
            self.button(starters, prompt, lambda prompt=prompt, **e: ask(prompt))
        render()

    def summaries(self, **event):
        self.panel.clear()
        selector = anvil.DropDown(items=anvil.server.call("list_documents"), placeholder="Choose a document")
        self.panel.add_component(selector)
        output = anvil.ColumnPanel(background="#ffffff")
        question = anvil.TextArea(placeholder="Ask a follow-up question about the summarized document")

        def render():
            output.clear()
            for prompt, result in self.summary_history:
                self.show_answer(output, prompt, result)

        def ask_summary(followup):
            title = selector.selected_value
            if not title or (followup and title != self.summary_title):
                anvil.alert("Select a document and generate its summary first.")
                return
            prompt = (question.text or "") if followup else "Write a plain-language executive summary of " + title
            context = [turn for q, result in self.summary_history[-4:] for turn in (
                {"role": "user", "content": q}, {"role": "assistant", "content": result["text"]},
            )] if followup else []
            result = anvil.server.call("answer", prompt, context, title)
            if "error" in result:
                anvil.alert(result["error"])
                return
            if not followup:
                self.summary_history.clear()
            self.summary_title = title
            self.summary_history.append((prompt, result))
            question.text = ""
            render()

        selector.selected_value = self.summary_title if self.summary_title in selector.items else None
        self.button(self.panel, "Generate executive summary", lambda **e: ask_summary(False), primary=True)
        self.panel.add_component(output)
        self.panel.add_component(question)
        self.button(self.panel, "Ask follow-up", lambda **e: ask_summary(True))
        render()

    def owner(self, **event):
        self.panel.clear()
        password = anvil.TextBox(hide_text=True, placeholder="Owner password")
        replace = anvil.CheckBox(text="Replace matching titles")
        pdfs = anvil.FileLoader(accept=".pdf", multiple=True)
        index = anvil.FileLoader(accept=".json")
        confirmation = anvil.TextBox(placeholder="Type CLEAR to confirm")
        self.panel.add_component(password)
        self.panel.add_component(replace)
        self.panel.add_component(anvil.Label(text="Upload PDF files"))
        self.panel.add_component(pdfs)

        def run(name, *args):
            try:
                result = anvil.server.call(name, password.text or "", *args)
                anvil.alert("\n".join(result) if result else "Collection cleared.")
            except Exception:
                anvil.alert("The operation failed. Check the owner password and the Anvil app logs.")
            finally:
                password.text = ""

        self.button(self.panel, "Index PDFs", lambda **e: run("upload_pdfs", pdfs.files, replace.checked))
        self.panel.add_component(anvil.Label(text="Import a Beacon Hill JSON index"))
        self.panel.add_component(index)
        self.button(self.panel, "Import index", lambda **e: run("import_index", index.file, replace.checked))
        self.panel.add_component(confirmation)
        self.button(self.panel, "Clear collection", lambda **e: run("clear_collection", confirmation.text))
