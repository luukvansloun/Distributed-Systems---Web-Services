from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import requests, math
from operator import itemgetter
from datetime import datetime

app = Flask(__name__)
CORS(app)
api = Api(app)

# De Lijn API Routing URLs
deLijnURLs = {
	"provinces": "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten",
	"linesForProvince": "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten/{entiteitnummer}/lijnen",
	"lineDirections": "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{entiteitnummer}/{lijnnummer}/lijnrichtingen",
	"lineRoute": "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{entiteitnummer}/{lijnnummer}/lijnrichtingen/{richting}/haltes",
	"serviceRoute": "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{entiteitnummer}/{lijnnummer}/lijnrichtingen/{richting}/dienstregelingen",
	"realtimeRoute": "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{entiteitnummer}/{lijnnummer}/lijnrichtingen/{richting}/real-time",
	"stopInfo": "https://api.delijn.be/DLKernOpenData/api/v1/haltes/{entiteitnummer}/{haltenummer}/dienstregelingen"
}

# HERE API Routing URL
routingURL = "https://route.api.here.com/routing/7.2/calculateroute.json?app_id=2UM7iHJDdS0W8vwG375U&app_code=Hk2AGPlB7ubKq3iuLpYaQQ&waypoint0=geo!{lat1},{lng1}&waypoint1=geo!{lat2},{lng2}&jsonAttributes=169&mode=fastest;car;traffic:disabled"

# HERE API Weather URL
weatherURL = "https://weather.cit.api.here.com/weather/1.0/report.json?product=observation&latitude={latitude}&longitude={longitude}&oneobservation=true&app_id=2UM7iHJDdS0W8vwG375U&app_code=Hk2AGPlB7ubKq3iuLpYaQQ"

headers = {
	"Ocp-Apim-Subscription-Key": "e855ca5e78074b8ca624b4a09c830985"
}

# Get all Provinces
class getProvinces(Resource):
	def get(self):
		return requests.get(url=deLijnURLs["provinces"], headers=headers).json()

# Get all Lines in a specific Province
class getLinesForProvince(Resource):
	def get(self, provinceNumber):
		requestData = requests.get(url=deLijnURLs["linesForProvince"].format(entiteitnummer=provinceNumber),
									headers=headers).json()

		lines = []
		for line in requestData["lijnen"]:
			if line["publiek"]:
				lineData = {}
				lineData["linenumber"] = line["lijnnummer"]
				lineData["description"] = line["omschrijving"]
				lines.append(lineData)

		lines = sorted(lines, key=itemgetter('linenumber'))

		return jsonify({'lines' : lines})

# Retrieve the possible directions for the requested line
class getLineDirections(Resource):
	def get(self, provinceNumber, lineNumber):
		requestData = requests.get(url=deLijnURLs["lineDirections"].format(entiteitnummer=provinceNumber, lijnnummer=lineNumber),
									headers=headers).json()

		directions = []
		for direction in requestData["lijnrichtingen"]:
			dirData = {}
			dirData["direction"] = direction["richting"]
			dirData["destination"] = direction["bestemming"]
			directions.append(dirData)

		directions = sorted(directions, key=itemgetter('direction'))

		return jsonify({'directions': directions})

# Retrieve all the stops and their info for the requested line
class getLineRoute(Resource):
	def get(self, provinceNumber, lineNumber, direction):
		# Request the different data
		requestData = requests.get(url=deLijnURLs["lineRoute"].format(entiteitnummer=provinceNumber, lijnnummer=lineNumber,
									richting=direction), headers=headers).json()

		sortData = requests.get(url=deLijnURLs["serviceRoute"].format(entiteitnummer=provinceNumber, lijnnummer=lineNumber,
									richting=direction), headers=headers).json()

		# Setup stop collection
		stops = []
		for i in range(len(requestData["haltes"])):
			stopData = {}
			stopData["stopNumber"] = requestData["haltes"][i]["haltenummer"]
			stopData["description"] = requestData["haltes"][i]["omschrijving"]

			lng = str(requestData["haltes"][i]["geoCoordinaat"]["longitude"])
			lat = str(requestData["haltes"][i]["geoCoordinaat"]["latitude"])
			stopData["latitude"] = lat
			stopData["longitude"] = lng

			stopData["weather_description"] = requests.get(url=weatherURL.format(latitude=lat, longitude=lng)).json()["observations"]["location"][0]["observation"][0]["description"]
			stopData["weather_temp"] = requests.get(url=weatherURL.format(latitude=lat, longitude=lng)).json()["observations"]["location"][0]["observation"][0]["temperature"]
			stopData["weather_icon"] = requests.get(url=weatherURL.format(latitude=lat, longitude=lng)).json()["observations"]["location"][0]["observation"][0]["iconLink"]
			stopData["waypoints"] = []

			stops.append(stopData)
		sortedStops = []

		# Sort the stops according to the service route
		for item in sortData["ritDoorkomsten"][0]["doorkomsten"]:
			for stop in stops:
				if item["haltenummer"] == stop["stopNumber"]:
					sortedStops.append(stop)

		waypoints = []
		# Setup waypoints for route
		for i in range(len(sortedStops)):
			if i < len(sortedStops) - 1:
				lng1 = sortedStops[i]["longitude"]
				lat1 = sortedStops[i]["latitude"]
				lng2 = sortedStops[i + 1]["longitude"]
				lat2 = sortedStops[i + 1]["latitude"]

				routingData = requests.get(url=routingURL.format(lat1=lat1, lng1=lng1, lat2=lat2, lng2=lng2)).json()

				for wp in routingData["route"][0]["waypoint"]:
					locationData = {}
					locationData["lng"] = wp["mappedPosition"]["longitude"]
					locationData["lat"] = wp["mappedPosition"]["latitude"]
					sortedStops[i]["waypoints"].append(locationData)
					waypoints.append(locationData)

		# Setup real time busses
		busses = []

		now = datetime.now()
		deLijnTimeFormat = "%Y-%m-%dT%H:%M:%S"

		for ride in sortData["ritDoorkomsten"]:
			rideStops = []
			for r in ride["doorkomsten"]:
				if r.get("dienstregelingTijdstip"):
					rideStops.append(r["dienstregelingTijdstip"])

			rideStops.sort()		
			stopOne = datetime.strptime(rideStops[0], deLijnTimeFormat)
			stopTwo = datetime.strptime(rideStops[-1], deLijnTimeFormat)

			if now >= stopOne and now <= stopTwo:
				diffOne = now - stopTwo
				diffTwo = stopTwo - stopOne
				ratio = diffOne / diffTwo

				base = (len(waypoints) - 1) * ratio
				floor = math.floor((len(waypoints) - 1) * ratio)
				ceiling = math.ceil((len(waypoints) - 1) * ratio)

				ratioDifference = base - floor

				leftBorder = [waypoints[floor]["lng"], waypoints[floor]["lat"]]
				rightBorder = [waypoints[ceiling]["lng"], waypoints[ceiling]["lat"]]

				busInfo = {}
				busInfo["longitude"] = leftBorder[0] + ((rightBorder[0] - leftBorder[0]) * ratioDifference)
				busInfo["latitude"] = leftBorder[1] + ((rightBorder[1] - leftBorder[1]) * ratioDifference)
				busses.append(busInfo)

		returnData = {
			"stops": sortedStops,
			"busses": busses
		}

		return jsonify(returnData)


# Add API resources
api.add_resource(getProvinces, '/provinces')
api.add_resource(getLinesForProvince, '/provinces/<provinceNumber>/lines')
api.add_resource(getLineDirections, '/<provinceNumber>/lines/<lineNumber>/directions')
api.add_resource(getLineRoute, '/<provinceNumber>/lines/<lineNumber>/directions/<direction>')

if __name__ == "__main__":
	app.run(host="0.0.0.0", port="3000")