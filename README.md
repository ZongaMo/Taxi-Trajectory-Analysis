# Taxi-Trajectory-Analysis

[中文](./README_CN.md)

## 1. Data Configuration
### 1.1. Project Description
[Data Files 01.zip – 014.zip](http://research.microsoft.com/apps/pubs/?id=152883)

After unzipping these data files, you will get 10,375 txt files (total 766 MB). These files record GPS trajectory data of 10,000 taxis in Beijing over a period of one week. The record format is as follows:
```
1,2008-02-02 15:36:08,116.51172,39.92123
1,2008-02-02 15:46:08,116.51135,39.93883
1,2008-02-02 15:46:08,116.51135,39.93883
…
```
Each record corresponds to a spatiotemporal point, containing user ID, time, longitude, and latitude. Please conduct taxi trajectory analysis based on this data.

### 1.2. Data Overview
This dataset contains GPS trajectory data of 10,357 taxis in Beijing from February 2 to February 8, 2008. The dataset includes approximately 15 million trajectory points, with a total trajectory mileage of 9 million kilometers. Figure 1 shows the distribution of time intervals and distance intervals between consecutive points, with an average sampling interval of about 177 seconds and an average distance interval of about 623 meters. Each file is named after a taxi ID and contains trajectory data for a single vehicle. Figure 2 visually displays the density distribution of GPS points in the dataset.
![Image failed to load](src/assets/README/image.png)

## 2. Technical Framework
- **Backend**: Python-based data algorithms, including data structure design, storage, transmission, query, search, and analysis for subsequent tasks.
  - Written as **callable functions** for deployment
  - <u>**All returned results need to be converted to JSON format**</u>
  - Need to write **simple API documentation** introducing *parameter configuration*, *return value structure*, and other notes for quick use;
  - **Data compression optimization**: For example, removing duplicate data points with no movement, keeping only the start and end points.

- **Frontend**: Vue2-based visual web page, which can be independently designed and completed;

- **All team members**: Write the **public part** of the course design report for their own designed parts in the shared document. Personal parts will be written after the development is completed. The public parts include:
  - 1. Background of the topic (all)
  - 2. Scheme demonstration (all)
  - 3. Process discussion (interaction between frontend and backend)
  - 4. Result analysis (to be discussed)

## 3. Functional Requirements
#### F1. Taxi Trajectory Visualization *(Frontend implemented, waiting for backend data API design)*
Display trajectories of **all** or **specific** taxis.
- Using **Tencent Maps** JavaScript API, as other map APIs require payment
- Expected effect:
![Image failed to load](src/assets/README/image-2.png)
##### (1) Required API:
  - **Parameters**: <u>Array of taxi IDs</u>;
  - **Return value**: 
    - **When parameters are provided**: Returns an **array** of TrailLine objects corresponding to the taxis with IDs in the parameter array
    - **When no parameters are provided or the parameter is an empty array**: Returns paths for **all** taxis, as a TrailLine array, where each TrailLine corresponds to a taxi;
    - Each TrailPoint in TrailLine contains latitude, longitude, and **timestamp**;
    - ***The data volume is huge, so optimization algorithms may be needed, such as using trajectory point thinning algorithms (like Douglas-Peucker) to simplify paths.***

##### (2) Required data format:
  - [TrailLine Array](https://lbs.qq.com/webApi/visualizationApi/visualizationDoc/visualizationDocTrail#3)
  - [Data Sample](https://mapapi.qq.com/web/lbs/visualizationApi/demo/data/trail.js) (for reference only, no timestamp, not our ideal data structure)

##### (3) Notes:
- Consider whether anomaly points need to be cleaned
- Return value when query results are empty

---
#### F2. Map Zoom Function *(Implemented)*
Can zoom in or out on the map and adjust the display of taxi trajectories accordingly.

---
#### F3. Regional Range Search
Count the **number** of taxis in a **user-specified rectangular area** during a **specific time period**. The rectangular area can be determined by **providing** the latitude and longitude **coordinates** of the upper-left and lower-right corners of the rectangle.

The frontend considers directly implementing rectangle selection on the map in the later stage, and then searching based on coordinates, which has no impact on the backend.

##### Required API:
  - **Parameters**: Time period, <u>Area</u>; (Parameters with <u>underscore</u> are optional, default to no limitation if not provided)
    - Time period
    ```
      {
      "startTime": format to be determined  // specified in API documentation and comments
      "endTime": same format as above
      }
    ```
    - Area
    ```
      {
      "ltPoint": format to be determined  // specified in API documentation and comments
       "rbPoint": format to be determined  // specified in API documentation and comments
      }
    ```
  
  - **Return value**: dict
  ```
    {
     "total": Number,
     "path": TrailLine[] // Can intercept the trajectory of each trail corresponding to the time period to reduce the amount of transmitted data
    }
  ```

##### Performance Optimization:
  Consider building appropriate <u>**indexes**</u> to speed up queries;

---
#### F4. Regional Traffic Density Analysis
- Given a distance parameter r, divide the entire map into grids, each grid size is r*r.
Statistically analyze changes in traffic density across all grid areas during different time periods.
- Expected effect:
![Image failed to load](src/assets/README/image-1.png)

##### Required API:
  - **Parameters**: Grid width
  - **Return value**: [HeatPoint Array](https://lbs.qq.com/webApi/visualizationApi/visualizationDoc/visualizationDocHeat#3)

---
#### F5. Regional Correlation Analysis 1
- User specifies two rectangular areas
Statistics on changes in traffic flow **between these two areas** during different time periods.

#### F6. Regional Correlation Analysis 2
- User specifies a rectangular area
Statistics on changes in traffic flow **between this rectangular area and other areas** over time.
- Expected effect diagrams might be as follows:
![Image failed to load](src/assets/README/image-3.png) ![Image failed to load](src/assets/README/image-4.png)

##### Required API:
  - **Parameters**: Time period, area1, <u>area2</u> (Parameters with <u>underscore</u> are optional, default to no limitation if not provided, i.e., F6)
  - **Return value**: Array
  ```
  [{"timeStamp": custom time format,
     "flowIn": Number,
     "flowOut": Number  // In and Out are relative to area1
  },{...},...]
  ```

##### Performance Optimization:
- Based on **state machine** to identify A→B movement sequences.
- Optimize correlation query performance to avoid full table scans.

**The following issues need to be resolved**
---

#### F7. Frequent Path Analysis 1
The **frequency** of a path can be defined as the total number of cars traveling on that path.
Based on user-given parameters k and distance parameter x, count the top k most frequent paths in the entire city with length exceeding x.

#### F8. Frequent Path Analysis 2
Given two rectangular areas A and B, analyze the top k most frequent travel paths from A to B.

##### Suggestions for data science:
- 1. Path clustering:
Use trajectory clustering algorithms (such as TRACLUS) to identify similar paths.
- 2. Frequency calculation:
Count the number of vehicles for each path, take Top-K.
- 3. Visualization:
Highlight frequent paths on the map and mark the number of trips.
- Technical points:
  - Path similarity calculation using DTW or LCSS algorithms.
  - Using Spark MLlib for distributed clustering in big data scenarios.

---
#### F9. Travel Time Analysis
Given two rectangular areas A and B, analyze the **shortest travel time path** for taxis from A to B during different time periods, as well as the corresponding **travel time**.

##### Suggestions for data science:
- 1. OD point filtering:
Filter all trajectory segments starting in A and ending in B.

- 2. Shortest time path:
Calculate the travel time for each trajectory segment by time period (end time - start time).
Take the path with the shortest time as the recommended path.

- 3. Visualization:
Draw the shortest time path on the map and mark the average travel time.

- Technical points:
  - Exclude abnormal time differences (such as exceeding 24 hours).
  - Dynamically update the shortest path by combining real-time traffic data.