# CV Job Matcher

CV Job Matcher is an Agentic AI application that reads your CV and finds relevant job openings from the web. This project leverages natural language processing and web scraping to match your skills and experiences with the best job opportunities available online.

## Features

- **Agent 1 (CV Parsing)**: Agent 1 extracts relevant information from your CV.
- **Agent 2 (Job Matching)**: Agent 2 Searches the internet for job openings that match your profile.
- **Customizable**: Allows customization of search criteria and preferences.

## Installation

To run this project, you need Python installed on your machine. Follow the steps below to set up the project:

1. Clone the repository:
   ```bash
   git clone https://github.com/rsachint/genAI_experiments.git
   cd genAI_experiments/cv-job-matcher
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place your CV & job_search_results.txt file in the `cv-job-matcher` directory.
2. Change the prompts for both Agent 1,2 in the matchCVToJobs.py file to make sure they work as per your expectations.
3. Run the application:
   ```bash
   python main.py
   ```
3. Follow the on-screen instructions to get job matches.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

Feel free to adjust the content as needed based on the specific details and requirements of your project.
