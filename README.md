# Security Log Analysis Dashboard

A comprehensive web-based dashboard for analyzing Apache web server security logs, built using AWS services, Elasticsearch, and Flask.

## Project Overview

This Security Log Analysis Dashboard processes and visualizes Apache web server logs to provide security insights and identify potential threats. The dashboard offers a comprehensive view of server activity, error patterns, and potential security incidents through intuitive visualizations.

## Features

- **Summary Statistics**: At-a-glance view of total logs, error rates, and potential attack counts
- **Time-Based Analysis**: Interactive charts showing request volume and error responses over time
- **IP-Based Analysis**: Visualization of top source IP addresses making requests to your server
- **Response Analysis**: HTTP status code distribution to identify unusual response patterns
- **Security Analysis**: Detection and visualization of potential attack patterns in request URLs
- **Search Functionality**: Ability to search and filter logs based on various criteria

## Architecture

The system follows an ETL (Extract, Transform, Load) pipeline architecture:

1. **Data Storage**: Raw Apache logs are stored in AWS S3
2. **Data Cataloging**: AWS Glue Crawler catalogs the raw log data
3. **Data Processing**: AWS Glue ETL job transforms raw logs into structured data with security metrics
4. **Indexing**: Transformed data is indexed in Elasticsearch for fast querying
5. **Visualization**: Flask web application queries Elasticsearch and renders the dashboard

## Technologies Used

- **AWS S3**: Storage for raw and transformed log data
- **AWS Glue**: Data cataloging and ETL processing
- **Elasticsearch**: Fast indexing and searching of log data
- **Flask**: Web application framework
- **Chart.js**: JavaScript library for interactive data visualizations
- **Bootstrap**: Frontend styling and responsive design

## Setup Instructions

### Prerequisites

- AWS Account with access to S3 and Glue services
- Elasticsearch (local installation or AWS Elasticsearch Service)
- Python 3.6+ with pip
- Apache log files (sample provided)

### Installation Steps

1. **Clone the repository**
  ```bash
  git clone https://github.com/yourusername/security-log-dashboard.git
  cd security-log-dashboard