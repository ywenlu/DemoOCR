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
import os
import flask

from TesseractOCR import show_ocr

external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([

    html.Div(

        [   html.Div(html.H1("OCR Demo", style={'margin':'10px'}), className="row text-white bg-dark", style={'height':'10vh'}),
            dcc.Upload(
                id='upload-image',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '5vh',
                    'lineHeight': '60px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                # Allow multiple files to be uploaded
                multiple=True),

            html.Div([
                html.Div([
                    dcc.Loading(id="loading-1", children=[
                        html.Div(id='output-image-upload', style={'height':'70vh', 'overflow': 'scroll'})
                    ], type='circle'),
                ], className="col-6 border px-1"),

                html.Div([
                    dcc.Loading(id="loading-2", children=[
                        html.Iframe(id='ocr-conversion-output', src='static/blank.html',
                                    className="col-12", style={'height':'70vh','borderWidth': '0px'})
                    ], type='circle'),
                ], className="col-6 border px-1"),
            ], className="row h-90", style={'height':'70vh'}),

            html.Div(
                [
                    html.Div([
                        html.Button(id='submit-button', n_clicks=0, children='Submit', className="btn btn-secondary col-6",
                                    style={'width': '100%', 'margin': '10px'})],
                        className="col-6"),

                    html.Div([
                        dcc.Loading(id="loading-3", children=[
                                html.Div(id='ocr-export-output', style={'width': '100%'}, className='row')
                            ], type="circle")
                        ],
                        className='col-6'
                    )


                ],
                className='row h-10', style={'height': '10vh', 'margin':'10px'}
            )

        ], className="container-fluid", style={'height': '80vh', 'margin':'10px'})
        ]
    )



def parse_contents(contents, filename, date):
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents, style={'width': '100%'}),
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


# @app.callback(Output('ocr-conversion-output', 'children'),
#               [Input('submit-button', 'n_clicks')],
#               [State('upload-image', 'contents')]
#               )
# def ocr_conversion(n_clicks, contents):
#     try:
#         msg = base64.b64decode(contents[0].split(',')[1])
#         buf = io.BytesIO(msg)
#         transcript = pytesseract.image_to_string(Image.open(buf))
#     except TypeError:
#         transcript = "Please upload a file"
#     return transcript


@app.callback([Output('ocr-export-output', 'children'),
              Output('ocr-conversion-output', 'src')],
              [Input('submit-button', 'n_clicks')],
              [State('upload-image', 'contents')]
              )
def ocr_export(n_clicks, contents):
    output = {}
    try:
        msg = base64.b64decode(contents[0].split(',')[1])
        buf = io.BytesIO(msg)
        export_btns = []
        for pdf_or_html in ['pdf','hocr']:
            output[pdf_or_html] = pytesseract.image_to_pdf_or_hocr(Image.open(buf), extension=pdf_or_html)
            if pdf_or_html=='pdf':
                btnname = 'Export PDF'
                fn = "ocr_output.pdf"
                filepath = "static/"+ fn
                f = open(filepath, "w+b")
                f.write(bytearray(output[pdf_or_html]))
            else:
                btnname = 'Export HTML'
                fn = "ocr_output.html"
                filepath = "static/" +fn
                f = open(filepath, "w+b")
                f.write(output[pdf_or_html])
            f.close()
            export_btn = html.A(btnname, href=filepath, target="_blank",
                                download=fn, className="btn btn-primary col-4", style={'margin':'10px', 'marginLeft':'20px', 'marginRight':'20px'})
            export_btns.append(export_btn)
        src = 'static/ocr_output.html'
    except TypeError:
        export_btns = html.A('')
        src = 'static/blank.html'
    return export_btns, src


@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return flask.send_from_directory(static_folder, path)

if __name__ == '__main__':
    app.run_server(debug=True)