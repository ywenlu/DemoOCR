import datetime
# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pytesseract
from PIL import Image
import io
from io import BytesIO, StringIO
import urllib

import base64
from IPython import display
import os
import cv2
from luminoth import Detector, read_image, vis_objects
from TesseractOCR import show_ocr
import json


def fig_to_uri(in_fig, close_all=True, **save_args):
    # type: (plt.Figure) -> str
    """
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)


def array_to_uri(img_array):
    # TODO convert directly np.array to uri string
    # type: (np.array) -> str
    """
    Save an image array as a URI
    """
    if len(img_array.shape) > 3:
        img_array = img_array[:, :, :3]

    im = Image.fromarray(img_array)
    im.save('buf.jpg')
    image = open('buf.jpg', 'rb')
    image_read = image.read()
    image64encoding = base64.b64encode(image_read).decode("ascii").replace("\n", "")
    image_uri = f"data:image/png;base64,{image64encoding}"
    return image_uri


def uri_to_array(content):
    # type: str -> (np.array)
    """
    Save a URI as an image array
    """
    msg = base64.b64decode(content.split(',')[1])
    buf = BytesIO(msg)
    img_array = np.ascontiguousarray(Image.open(buf))

    if len(img_array.shape) < 3:
        img_array = np.repeat(img_array[:, :, np.newaxis], 3, axis=2).astype(np.uint8) * 255
    return img_array


# Creat checkpoint
detector = Detector(checkpoint='6398676e0ced')


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
            'width': '95%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    html.Div([
        html.Button(id='submit-button', n_clicks=0, children='Submit', className="btn btn-secondary",
                    style={'width': '100%', 'marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 10}),
    ], className="col-2"),

    html.Div([
        html.Div([
            dcc.Loading(id="loading-1", children=[
                html.Div(id='output-image-upload', style={'width': '100%'})
            ], type='circle'),
        ], className="col-4"),

        html.Div([
            dcc.Loading(id="loading-2", children=[
                html.Div(id='output-image-table-windows', style={'width': '100%'})
            ], type='circle'),
        ], className="col-4"),

        html.Div([
            dcc.Loading(id="loading-3", children=[
                html.Div(id='ocr-conversion-output', style={'width': '90%'})
            ], type='circle'),
            dcc.Loading(id="loading-4", children=[
                html.Div(id='ocr-export-output', style={'width': '100%'})
            ], type="circle"),
            # html.Button(id='export-pdf-button', n_clicks=0, children='Export PDF'),
            # html.Button(id='export-html-button', n_clicks=0, children='Export HTML')
        ], className="col-4"),

    ], className="row"),

])


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


def table_windows_contents(content):
    img_array = uri_to_array(content)


    img = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    b = cv2.distanceTransform(img, distanceType=cv2.DIST_L2, maskSize=5)
    g = cv2.distanceTransform(img, distanceType=cv2.DIST_L1, maskSize=5)
    r = cv2.distanceTransform(img, distanceType=cv2.DIST_C, maskSize=5)

    # merge the transformed channels back to an image to predict
    image_map = cv2.merge((b, g, r))
    objects = detector.predict(image_map)
    objects_json = json.dumps(objects)
    img_windows = vis_objects(img_array, objects, scale=2, fill=100)
    img_windows_array = np.array(img_windows)

    img_uri = array_to_uri(img_windows_array)

    return html.Div([
        html.H5('Tables detection'),
        # html.H6(datetime.datetime.fromtimestamp(date)),

        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=img_uri, style={'width': '100%'}),
        html.Hr(),
        html.Div('List of table windows'),
        html.Pre(objects_json, style={
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


@app.callback(Output('output-image-table-windows', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('upload-image', 'contents')])
def update_table_windows(n_clicks, list_of_contents):
    try:

        children = [
            table_windows_contents(c) for c in list_of_contents
        ]

    except:
        children = "Please upload a file"

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
    try:
        msg = base64.b64decode(contents[0].split(',')[1])
        buf = io.BytesIO(msg)
        export_btns = []
        for pdf_or_html in ['pdf', 'hocr']:
            pdf_or_html_output = pytesseract.image_to_pdf_or_hocr(Image.open(buf), extension=pdf_or_html)
            if pdf_or_html == 'pdf':
                btnname = 'Export PDF'
                fn = "ocr_output.pdf"
                filepath = "static/" + fn
                f = open(filepath, "w+b")
                f.write(bytearray(pdf_or_html_output))
            else:
                btnname = 'Export HTML'
                fn = "ocr_output.html"
                filepath = "static/" + fn
                f = open(filepath, "w+b")
                f.write(pdf_or_html_output)
            f.close()
            export_btn = html.A(btnname, href=filepath, target="_blank",
                                download=fn, className="btn btn-primary",
                                style={'width': '90%', 'marginTop': 10, 'marginBottom': 10})
            export_btns.append(export_btn)
    except TypeError:
        export_btns = html.A('')
    return export_btns

    # return html.A('Export PDF', href="static/ocr_output.pdf", target="_blank", download="rawdata.pdf")#('n_clicks {}'.format(n_clicks))

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
