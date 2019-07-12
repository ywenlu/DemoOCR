import datetime

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import base64
import io
import pytesseract
from PIL import Image
import urllib

from TesseractOCR import show_ocr

external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Upload(
        id='upload-image',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div([
        html.Div([
            dcc.Loading(id="loading-1", children=[html.Div(id='output-image-upload')], type='circle'),
            html.Button(id='submit-button', n_clicks=0, children='Submit')
        ], className="col-6"),
        html.Div([
            dcc.Loading(id="loading-2", children=[html.Div(id='ocr-conversion-output')], type='circle'),
            dcc.Loading(id ="loading-3", children=[html.Div(id='ocr-export-output')],type="circle")
            # html.Button(id='export-pdf-button', n_clicks=0, children='Export PDF'),
            # html.Button(id='export-html-button', n_clicks=0, children='Export HTML')
        ], className="col-6"),
    ], className="row"),


    ])


def parse_contents(contents, filename, date):
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents),
        html.Hr(),
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])


@app.callback(Output('output-image-upload', 'children'),
              [Input('upload-image', 'contents')],
              [State('upload-image', 'filename'),
               State('upload-image', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


@app.callback(Output('ocr-conversion-output', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('upload-image', 'contents')]
              )
def ocr_conversion(n_clicks, contents):
    try:
        msg = base64.b64decode(contents[0].split(',')[1])
        buf = io.BytesIO(msg)
        transcript = pytesseract.image_to_string(Image.open(buf))
    except:
        transcript = "Please upload a file"
    return transcript


@app.callback(Output('ocr-export-output', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('upload-image', 'contents')]
              )
def ocr_export(n_clicks, contents):
    # pdf_or_html = 'html'
    # pdf_or_html_output = pytesseract.image_to_pdf_or_hocr(Image.open(filename[0]), extension=pdf_or_html)
    # filepath = "image/ocr_output." + pdf_or_html
    # f = open(filepath, "w+b")
    # f.write(bytearray(pdf_or_html_output))
    # return html.A('Export PDF', id='exportPDF', className='btn btn-primary', href="image/ocr_output.html", target="_blank", download="rawdata.pdf",)
    try:
        msg = base64.b64decode(contents[0].split(',')[1])
        buf = io.BytesIO(msg)
        export_btns = []
        for pdf_or_html in ['pdf','hocr']:
            pdf_or_html_output = pytesseract.image_to_pdf_or_hocr(Image.open(buf), extension=pdf_or_html)
            if pdf_or_html=='pdf':
                btnname = 'Export PDF'
                fn = "ocr_output.pdf"
                filepath = "static/"+ fn
                f = open(filepath, "w+b")
                f.write(bytearray(pdf_or_html_output))
            else:
                btnname = 'Export HTML'
                fn = "ocr_output.html"
                filepath = "static/" +fn
                f = open(filepath, "w+b")
                f.write(pdf_or_html_output)
            f.close()
            export_btn = html.A(btnname, href=filepath, target="_blank", download=fn, className="btn btn-primary")#('n_clicks {}'.format(n_clicks))
            export_btns.append(export_btn)
    except TypeError:
        export_btns = html.A('')
    return export_btns

    #return html.A('Export PDF', href="static/ocr_output.pdf", target="_blank", download="rawdata.pdf")#('n_clicks {}'.format(n_clicks))


    # export_buttons = []
    # try:
    #     for pdf_or_html in ['pdf','html']:
    #         pdf_or_html_output = pytesseract.image_to_pdf_or_hocr(Image.open(filename[0]), extension=pdf_or_html)
    #         filepath = "image/ocr_output." + pdf_or_html
    #         export_buttons.append(filepath)
    #         f = open(filepath, "w+b")
    #         f.write(bytearray(pdf_or_html_output))
    #         f.close()
    #     return html.Div(html.A('hello',color='blue'))  #export_buttons[0]
    # except:
    #     export_buttons = []
    #     pass

@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)

if __name__ == '__main__':
    app.run_server(debug=True)