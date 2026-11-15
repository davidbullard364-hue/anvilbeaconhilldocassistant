from ._anvil_designer import Form1Template
import anvil
from anvil.js import get_dom_node, window
import anvil.media
import anvil.server


STYLES = """
.bh-app {
  --bh-ink: #252821;
  --bh-green: #3b5042;
  --bh-border: #ddd5c4;
  --bh-paper: #fcfaf5;
  --bh-gray: #eeece6;
  color: var(--bh-ink);
  font-family: "DM Sans", system-ui, sans-serif;
  max-width: 1500px;
  margin: 0 auto;
  padding: clamp(8px, 2.3vw, 30px);
}
.bh-app .bh-hero {
  padding: clamp(24px, 4vw, 58px);
  background: linear-gradient(110deg, #fcfaf5, #efe7d4);
  border: 1px solid var(--bh-border);
  border-left: 5px solid #a48159;
  border-radius: 24px;
  box-shadow: 0 12px 32px #342d1910;
}
.bh-app .bh-hero h1 {
  font-family: "DM Serif Text", Georgia, serif;
  font-size: clamp(2rem, 4.35vw, 4.5rem);
  line-height: 1.06;
  color: var(--bh-ink);
  margin: 0 0 .55em;
}
.bh-app .bh-hero p { font-size: 1.05rem; line-height: 1.6; max-width: 65ch; }
.bh-app .bh-nav { border-bottom: 1px solid #77736b; margin: 22px 0 18px; }
.bh-app .bh-tab button, .bh-app button.bh-tab {
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--bh-ink);
  box-shadow: none;
  text-transform: none;
  letter-spacing: normal;
  padding: .55rem 1rem;
}
.bh-app .bh-tab-active button, .bh-app button.bh-tab-active {
  background: var(--bh-green);
  color: white;
}
.bh-app .bh-card, .bh-app .bh-sidebar {
  padding: clamp(14px, 2vw, 25px);
  background: var(--bh-paper);
  border: 1px solid var(--bh-border);
  border-radius: 20px;
}
.bh-app .bh-card { box-shadow: 0 10px 30px #342d190c; line-height: 1.65; }
.bh-app .bh-card h2 { margin-top: 0; }
.bh-app .bh-sidebar { padding: 14px; }
.bh-app .bh-sidebar-title { color: var(--bh-green); }
.bh-app .bh-prompt button, .bh-app button.bh-prompt {
  width: 100%;
  text-align: left;
  white-space: normal;
  text-transform: none;
  letter-spacing: normal;
  background: var(--bh-gray);
  color: var(--bh-ink);
  border: 0;
  border-radius: 9px;
  padding: .55rem .7rem;
}
.bh-app .bh-ask button, .bh-app button.bh-ask {
  background: var(--bh-green);
  color: white;
  border-radius: 9px;
  text-transform: none;
  width: 100%;
}
.bh-app .bh-input textarea, .bh-app textarea.bh-input {
  background: var(--bh-gray);
  color: var(--bh-ink);
  border: 1px solid #bab5a9;
  border-radius: 9px;
  min-height: 78px;
  padding: .75rem;
}
.bh-app .bh-conversation, .bh-app .bh-summary-output {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--bh-border);
  overflow-wrap: anywhere;
}
.bh-app .bh-conversation { min-height: 340px; background: var(--bh-gray); }
.bh-app .bh-summary-output { background: white; }
.bh-app .bh-note { color: #5a574e; margin-top: 12px; }
@media (max-width: 700px) {
  .bh-app .bh-chat-layout [class*="col-xs-"] {
    width: 100%;
    margin-left: 0;
  }
  .bh-app .bh-sidebar { margin-top: 12px; }
}
"""


class Form1(Form1Template):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.clear()
        self.background = "#ffffff"
        self.history = []
        self.last_question = None
        self.summary_history = []
        self.summary_title = None
        self.tabs = {}

        document = window.document
        if not document.getElementById("beacon-hill-theme"):
            style = document.createElement("style")
            style.id = "beacon-hill-theme"
            style.textContent = STYLES
            document.head.appendChild(style)
        self.style(self, "bh-app")

        hero = anvil.RichText(format="markdown", content=(
            "# Beacon Hill Document Assistant\n\n"
            "Ask questions about community documents and get executive summaries with sources.\n\n"
            "**Community resource maintained by a resident.** "
            "Check cited documents when making decisions."
        ))
        self.add_component(hero)
        self.style(hero, "bh-hero")
        nav = anvil.FlowPanel()
        self.add_component(nav)
        self.style(nav, "bh-nav")
        for name, handler in [
            ("Welcome", self.welcome), ("Document Assistant", self.chat),
            ("Executive Summaries", self.summaries), ("Owner Tools", self.owner),
        ]:
            self.tabs[name] = self.button(nav, name, handler, css_class="bh-tab")

        self.panel = anvil.ColumnPanel()
        self.add_component(self.panel)
        self.welcome()

    def style(self, component, css_class):
        get_dom_node(component).classList.add(css_class)

    def select_tab(self, name):
        for label, button in self.tabs.items():
            classes = get_dom_node(button).classList
            if label == name:
                classes.add("bh-tab-active")
            else:
                classes.remove("bh-tab-active")
        self.panel.clear()

    def button(self, panel, title, handler, primary=False, css_class=None):
        button = anvil.Button(text=title)
        if css_class is None:
            button.background = "#3b5042" if primary else "#eeece6"
            button.foreground = "#ffffff" if primary else "#252821"
        button.set_event_handler("click", handler)
        panel.add_component(button)
        if css_class:
            self.style(button, css_class)
        return button

    def welcome(self, **event):
        self.select_tab("Welcome")
        guide = anvil.RichText(format="markdown", content=(
            "## Welcome to the Beacon Hill Document Assistant\n\n"
            "Explore community documents and find the sources behind each answer.\n\n"
            "### Document Assistant\n\n"
            "Ask a question in your own words or choose a starter question. The assistant searches "
            "the full collection. Ask follow-up questions, request a simpler explanation, "
            "or ask to see the supporting wording. Use the citations to check the source.\n\n"
            "### Executive Summaries\n\n"
            "Choose a document and select **Generate executive summary** for a plain-language "
            "overview with citations. Use the follow-up field to ask about that document."
        ))
        self.panel.add_component(guide)
        self.style(guide, "bh-card")
        note = anvil.Label(text="Answers are generated from the current collection. Interpretations may require further review.")
        self.panel.add_component(note)
        self.style(note, "bh-note")

    def show_answer(self, panel, question, result):
        panel.add_component(anvil.Label(text=question, bold=True))
        panel.add_component(anvil.RichText(format="markdown", content=result["text"]))
        for source in result["sources"]:
            title = source["title"]
            link = anvil.Link(text="[{}] {} · PDF page {}".format(
                source["number"], title, source["page"],
            ))
            link.set_event_handler("click", lambda title=title, **event: self.open_pdf(title))
            panel.add_component(link)

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
        self.select_tab("Document Assistant")
        layout = anvil.GridPanel()
        self.panel.add_component(layout)
        self.style(layout, "bh-chat-layout")
        controls = anvil.ColumnPanel()
        workspace = anvil.ColumnPanel()
        layout.add_component(controls, row="chat", col_xs=0, width_xs=3)
        layout.add_component(workspace, row="chat", col_xs=3, width_xs=9)
        self.style(controls, "bh-sidebar")

        composer = anvil.GridPanel()
        workspace.add_component(composer)
        fields = anvil.ColumnPanel()
        actions = anvil.ColumnPanel()
        composer.add_component(fields, row="question", col_xs=0, width_xs=10)
        composer.add_component(actions, row="question", col_xs=10, width_xs=2)
        fields.add_component(anvil.Label(text="Your question", bold=True))
        question = anvil.TextArea(placeholder="What would you like to understand?")
        fields.add_component(question)
        self.style(question, "bh-input")
        conversation = anvil.ColumnPanel()
        workspace.add_component(conversation)
        self.style(conversation, "bh-conversation")
        conversation.add_component(anvil.Label(text="Document conversation", bold=True))
        messages = anvil.ColumnPanel()
        conversation.add_component(messages)

        def render():
            messages.clear()
            for prompt, result in self.history:
                self.show_answer(messages, prompt, result)

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

        self.button(actions, "Ask", lambda **e: ask(question.text or ""), css_class="bh-ask")
        heading = anvil.Label(text="Try a question", bold=True)
        controls.add_component(heading)
        self.style(heading, "bh-sidebar-title")
        for prompt in (
            "How do I file a complaint?", "Summarize the bylaws",
            "What records does the association retain?", "Explain the conflict-of-interest policy",
        ):
            self.button(controls, prompt, lambda prompt=prompt, **e: ask(prompt), css_class="bh-prompt")

        heading = anvil.Label(text="Answer prompts", bold=True)
        controls.add_component(heading)
        self.style(heading, "bh-sidebar-title")
        for label, prompt in (
            ("Explain more simply", "Explain the previous answer more simply."),
            ("Show supporting wording", "Show the supporting wording."),
        ):
            self.button(controls, label, lambda prompt=prompt, **e: ask(prompt), css_class="bh-prompt")
        self.button(controls, "Retry last question", lambda **e: ask(self.last_question or ""), css_class="bh-prompt")
        self.button(controls, "New conversation", reset, css_class="bh-prompt")
        render()

    def summaries(self, **event):
        self.select_tab("Executive Summaries")
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
        self.panel.add_component(anvil.Label(text="Executive summary", bold=True))
        self.panel.add_component(output)
        self.style(output, "bh-summary-output")
        self.panel.add_component(question)
        self.style(question, "bh-input")
        followup_button = self.button(self.panel, "Ask follow-up", lambda **e: ask_summary(True))

        def change_document(**event):
            question.text = ""
            render()

        selector.set_event_handler("change", change_document)
        render()

    def owner(self, **event):
        self.select_tab("Owner Tools")
        owner_panel = anvil.ColumnPanel()
        self.panel.add_component(owner_panel)
        password = anvil.TextBox(hide_text=True, placeholder="Owner password")
        owner_panel.add_component(password)

        def unlock(**event):
            if not unlock_button.enabled:
                return
            candidate = password.text
            if not candidate:
                anvil.alert("Enter the owner password first.")
                return
            unlock_button.enabled = False
            try:
                accepted = self.call_server("unlock_owner_tools", candidate)
            finally:
                password.text = ""
                unlock_button.enabled = True
            if owner_panel.parent is not self.panel:
                return
            if accepted is True:
                self.show_owner_tools(owner_panel, candidate)
            elif accepted is False:
                anvil.alert("Incorrect owner password.")

        unlock_button = self.button(owner_panel, "Unlock Owner Tools", unlock, primary=True)
        password.set_event_handler("pressed_enter", unlock)

    def show_owner_tools(self, panel, owner_password):
        panel.clear()
        replace = anvil.CheckBox(text="Replace matching titles")
        pdfs = anvil.FileLoader(file_types=".pdf", multiple=True, show_state=True, text="Choose PDFs")
        index = anvil.FileLoader(file_types=".json")
        confirmation = anvil.TextBox(placeholder="Type CLEAR to confirm")

        def lock(**event):
            nonlocal owner_password
            owner_password = ""
            self.owner()

        def run(name, *args):
            result = self.call_server(name, owner_password, *args)
            if not result or panel.parent is not self.panel:
                return
            if result == ["Owner authentication failed."]:
                lock()
            anvil.alert("\n".join(result))

        def index_pdfs(**event):
            files = list(pdfs.files or [])
            if not files:
                anvil.alert("Choose at least one PDF first.")
                return
            if len(files) > 50:
                anvil.alert("Choose up to 50 PDFs at a time.")
                return
            replace_titles = replace.checked
            for control in upload_controls:
                control.enabled = False
            messages = []
            seen_titles = set()
            try:
                for position, file in enumerate(files, 1):
                    if panel.parent is not self.panel:
                        return
                    name = file.name or "Unnamed PDF"
                    title = name[:-4].strip().lower() if name.lower().endswith(".pdf") else None
                    if title and title in seen_titles:
                        messages.append("Skipped duplicate title in this selection: " + name)
                        continue
                    upload_status.text = "Indexing {}/{}: {}".format(position, len(files), name)
                    result = self.call_server("upload_pdfs", owner_password, [file], replace_titles)
                    if result is None:
                        messages.append("Stopped at " + name + ". Check the collection before retrying this file.")
                        break
                    messages.extend(result)
                    if result == ["Owner authentication failed."]:
                        if panel.parent is self.panel:
                            lock()
                            anvil.alert(result[0])
                        return
                    if title and result and result[0].startswith(("Added ", "Replaced ", "Skipped existing title ")):
                        seen_titles.add(title)
            finally:
                upload_status.text = ""
                for control in upload_controls:
                    control.enabled = True
            if messages and panel.parent is self.panel:
                anvil.alert("\n".join(messages))

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

        lock_button = self.button(panel, "Lock Owner Tools", lock)
        panel.add_component(replace)
        panel.add_component(anvil.Label(text="Upload PDF files"))
        panel.add_component(pdfs)
        index_button = self.button(panel, "Index PDFs", index_pdfs)
        upload_status = anvil.Label(text="")
        panel.add_component(upload_status)
        panel.add_component(anvil.Label(text="Import a Beacon Hill JSON index"))
        panel.add_component(index)
        import_button = self.button(panel, "Import index", import_json)
        panel.add_component(confirmation)
        clear_button = self.button(panel, "Clear collection", clear)
        upload_controls = (lock_button, index_button, import_button, clear_button, pdfs, replace)
