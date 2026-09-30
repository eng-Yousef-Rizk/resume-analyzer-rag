const btn = document.getElementById("analyzeBtn");
const resumeTextInput = document.getElementById("resumeText");

const resultDiv = document.getElementById("result");
const loadingDiv = document.getElementById("loading");
const errorDiv = document.getElementById("error");

const overallScore = document.getElementById("overallScore");
const strengthsList = document.getElementById("strengthsList");
const weaknessesList = document.getElementById("weaknessesList");
const suggestionsList = document.getElementById("suggestionsList");


btn.addEventListener("click", analyzeResume);


async function analyzeResume() {
    const resumeText = resumeTextInput.value.trim();

    // Validate input
    if (!resumeText) {
        showError("Please paste your resume text first.");
        return;
    }

    // Reset UI
    hideError();
    resultDiv.style.display = "none";
    loadingDiv.style.display = "block";

    btn.disabled = true;
    btn.textContent = "Analyzing...";

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                resume_text: resumeText
            })
        });

        // Handle HTTP errors
        if (!response.ok) {
            let errorMessage = `Server error (${response.status})`;

            try {
                const errorData = await response.json();

                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch {
                // Response wasn't JSON
            }

            throw new Error(errorMessage);
        }

        const data = await response.json();

        renderResult(data);

    } catch (error) {
        console.error("Resume analysis error:", error);

        showError(
            `Failed to analyze your resume. ${error.message}`
        );

    } finally {
        loadingDiv.style.display = "none";

        btn.disabled = false;
        btn.textContent = "Analyze Resume";
    }
}


function renderResult(data) {

    // Validate the response
    if (
        typeof data.overall_score !== "number" ||
        !Array.isArray(data.strengths) ||
        !Array.isArray(data.weaknesses) ||
        !Array.isArray(data.suggestions)
    ) {
        showError("The server returned an invalid analysis response.");
        return;
    }


    // Display overall score
    overallScore.textContent = `${data.overall_score}/10`;


    // Display strengths
    renderList(strengthsList, data.strengths);


    // Display weaknesses
    renderList(weaknessesList, data.weaknesses);


    // Display suggestions
    renderList(suggestionsList, data.suggestions);


    // Show results
    resultDiv.style.display = "block";


    // Scroll to results
    resultDiv.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


function renderList(listElement, items) {

    // Clear previous results
    listElement.innerHTML = "";

    items.forEach(item => {

        const li = document.createElement("li");

        // textContent prevents returned text from being
        // interpreted as HTML
        li.textContent = item;

        listElement.appendChild(li);
    });
}


function showError(message) {

    errorDiv.textContent = message;
    errorDiv.style.display = "block";

    resultDiv.style.display = "none";
}


function hideError() {

    errorDiv.textContent = "";
    errorDiv.style.display = "none";
}

