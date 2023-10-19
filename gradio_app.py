import gradio as gr
import privateGPT
import shutil
import features
import ingest


def add_text(history, text):
    history = history + [(text, None)]
    return history, gr.update(value="", interactive=False)


def add_file(history, file):
    history = history + [((file.name,), None)]
    return history


def bot(history):
    response = privateGPT.answer_f(history[-1][0])
    history[-1][1] = response
    return history


def save_file(history, directory, github, website):
    with open(directory, "w") as f:
        for entry in history:
            f.write(f"{entry[0]}: {entry[1]}")


def upload_file(file):
    custom_path = "D:/proj_tpo/private_ai/mv_privateGPT/upload_documents/data.png"
    shutil.copy2(file.name, custom_path)
    features.paddle_ocr(custom_path)


def add_website(website):
    try:
        if "https://github.com/" in website:
            features.get_repo(website)
        else:
            file_name = website.split("//")[1].split("/")[0]
            features.get_web_text(website, file_name)
    except Exception as e:
        print("invalid address")
        print(e)


def ingest_document():
    ingest.main()


with gr.Blocks() as demo:
    chatbot = gr.Chatbot([], elem_id="chatbot").style(height=580)
    privateGPT.main()
    with gr.Tab("Chat"):
        with gr.Column():
            txt = gr.Textbox(
                show_label=False,
                placeholder="Enter text and press enter, or upload an image",
            ).style(container=False)

    txt_msg = txt.submit(add_text, [chatbot, txt], [
                         chatbot, txt], queue=False).then(bot, chatbot, chatbot)
    txt_msg.then(lambda: gr.update(interactive=True), None, [txt], queue=False)

    with gr.Tab("Upload"):
        with gr.Row(max_height=4):
            with gr.Column():
                web_txt = gr.Textbox(
                    show_label=False,
                    placeholder="Enter website or github address",
                )

            with gr.Column():
                upload_button = gr.UploadButton(
                    "Click to Upload a File", file_types=["image"])
                upload_button.upload(upload_file, upload_button)

            ingest_button = gr.Button("Ingest")
            ingest_massage = ingest_button.click(ingest_document)

    web_msg = web_txt.submit(add_website, web_txt, web_txt, queue=False)


if __name__ == "__main__":
    demo.launch()
