import gradio as gr

def save_file(file):
   # save_to_database(file)
    return "File saved to database successfully!"
file_upload_interface = gr.Interface(
    fn=save_file,
    inputs=gr.inputs.File(label="Upload a file"),
    outputs="text",
    title="Upload a file to the database",
    description="Click the button below to upload a file to the database.",
    allow_flagging=False,
)