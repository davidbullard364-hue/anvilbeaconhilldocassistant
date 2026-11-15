from ._anvil_designer import Form1Template
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

    def call_server(self, name, *args):
        try:
            return anvil.server.call(name, *args)
        except anvil.server.ExecutionTerminatedError as error:
            print(error)
            anvil.alert("The server stopped during this request. Check the Anvil App Logs for details.")
        except Exception as error:
            print(error)
            anvil.alert("The request failed. Please try again.")
        return None

    def open_pdf(self, title):
        result = self.call_server("get_pdf", title)
        if result is None:
            return
        media = result.get("pdf")
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
            result = self.call_server("answer", prompt, history)
            if result is None:
                return
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
        titles = self.call_server("list_documents")
        if titles is None:
            return
        if not titles:
            self.panel.add_component(anvil.Label(text="There are no indexed documents yet."))
            return
        selector = anvil.DropDown(
            items=titles, include_placeholder=True, placeholder="Choose a document",
            selected_value=self.summary_title if self.summary_title in titles else None,
        )
        self.panel.add_component(selector)
        output = anvil.ColumnPanel(background="#ffffff")
        question = anvil.TextArea(placeholder="Ask a follow-up question about the summarized document")

        def render():
            output.clear()
            ready = selector.selected_value is not None and selector.selected_value == self.summary_title
            question.enabled = ready
            followup_button.enabled = ready
            if not ready:
                return
            for prompt, result in self.summary_history:
                self.show_answer(output, prompt, result)

        def ask_summary(followup):
            title = selector.selected_value
            if not title or (followup and title != self.summary_title):
                anvil.alert("Select a document and generate its summary first.")
                return
            prompt = (question.text or "") if followup else "Write a plain-language executive summary of " + title
            if not prompt.strip():
                anvil.alert("Enter a follow-up question first.")
                return
            context = [turn for q, result in self.summary_history[-4:] for turn in (
                {"role": "user", "content": q}, {"role": "assistant", "content": result["text"]},
            )] if followup else []
            result = self.call_server("answer", prompt, context, title)
            if result is None:
                return
            if "error" in result:
                anvil.alert(result["error"])
                return
            if not followup:
                self.summary_history.clear()
            self.summary_title = title
            self.summary_history.append((prompt, result))
            question.text = ""
            render()

        self.button(self.panel, "Generate executive summary", lambda **e: ask_summary(False), primary=True)
        self.panel.add_component(output)
        self.panel.add_component(question)
        followup_button = self.button(self.panel, "Ask follow-up", lambda **e: ask_summary(True))

        def change_document(**event):
            question.text = ""
            render()

        selector.set_event_handler("change", change_document)
        render()

    def owner(self, **event):
        self.panel.clear()
        owner_panel = anvil.ColumnPanel()
        self.panel.add_component(owner_panel)
        password = anvil.TextBox(hide_text=True, placeholder="Owner password")
        owner_panel.add_component(password)

        def unlock(**event):
            if not password.text:
                anvil.alert("Enter the owner password first.")
                return
            unlock_button.enabled = False
            try:
                accepted = self.call_server("unlock_owner_tools", password.text)
            finally:
                password.text = ""
                unlock_button.enabled = True
            if owner_panel.parent is not self.panel:
                return
            if accepted is True:
                self.show_owner_tools(owner_panel)
            elif accepted is False:
                anvil.alert("Incorrect owner password.")

        unlock_button = self.button(owner_panel, "Unlock Owner Tools", unlock, primary=True)
        password.set_event_handler("pressed_enter", unlock)

    def show_owner_tools(self, panel):
        panel.clear()
        replace = anvil.CheckBox(text="Replace matching titles")
        pdfs = anvil.FileLoader(file_types=".pdf", multiple=True)
        index = anvil.FileLoader(file_types=".json")
        confirmation = anvil.TextBox(placeholder="Type CLEAR to confirm")

        def lock(**event):
            if self.call_server("lock_owner_tools") is True and panel.parent is self.panel:
                self.owner()

        def run(name, *args):
            result = self.call_server(name, None, *args)
            if not result or panel.parent is not self.panel:
                return
            if result == ["Unlock Owner Tools to continue."]:
                self.owner()
            anvil.alert("\n".join(result))

        def index_pdfs(**event):
            if not pdfs.files:
                anvil.alert("Choose at least one PDF first.")
                return
            run("upload_pdfs", pdfs.files, replace.checked)

        def import_json(**event):
            if index.file is None:
                anvil.alert("Choose a JSON index file first.")
                return
            run("import_index", index.file, replace.checked)

        def clear(**event):
            if confirmation.text != "CLEAR":
                anvil.alert("Type CLEAR to confirm.")
                return
            run("clear_collection", confirmation.text)

        self.button(panel, "Lock Owner Tools", lock)
        panel.add_component(replace)
        panel.add_component(anvil.Label(text="Upload PDF files"))
        panel.add_component(pdfs)
        self.button(panel, "Index PDFs", index_pdfs)
        panel.add_component(anvil.Label(text="Import a Beacon Hill JSON index"))
        panel.add_component(index)
        self.button(panel, "Import index", import_json)
        panel.add_component(confirmation)
        self.button(panel, "Clear collection", clear)
