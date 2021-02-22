from flask import Flask, render_template, request, Response
import io
import os
from helper import *

app = Flask(__name__)

# main route
@app.route('/')
def main():
  return render_template("index.html")

# quick handle checkboxes
def checkbox(val):
  if val == 'true':
    return True
  elif val == 'false':
    return False

# generation route
@app.route('/generate', methods = ['POST', 'GET'])
def generate():
  # get arguments
  year = int(request.args.get('year'))
  lat = float(request.args.get('lat'))
  lon = float(request.args.get('lon'))
  width = int(request.args.get('width'))
  height = int(request.args.get('height'))
  use_dst = checkbox(request.args.get('use_dst'))
  sunrise_jump = float(request.args.get('sunrise_jump'))
  hue_shift = float(request.args.get('hue_shift'))

  # create pointer for generated file
  fp_img = io.BytesIO()

  # generate image with direct generation method
  arr_utc = time_arr(year, lon, lat, use_dst=use_dst)
  azi, alt = sun_positions(arr_utc, lon, lat)
  r, g, b = get_colors(azi, alt, sunrise_jump=sunrise_jump, hue_shift=hue_shift)
  pixels = stack_rgb(r, g, b)
  gen_png_to_stream(pixels, width, height, fp_img)

  # seek pointer to beginning before sending to client
  fp_img.seek(0)

  # send generated image to client
  return Response(fp_img, mimetype="image/png")

# run server
# if __name__ == '__main__':
#   app.run()
if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host = '0.0.0.0', port = port)