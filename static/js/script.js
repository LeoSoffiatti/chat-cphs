const uploadForm = document.getElementById('upload-form');
const fileUpload = document.getElementById('file-upload');
const uploadEvaluateBtn = document.getElementById('upload-evaluate-btn');
const uploadLabel = document.querySelector('.upload-label');
const overallScore = document.getElementById('overall-score');
const executiveSummary = document.getElementById('executive-summary');
const improvementPoints = document.getElementById('improvement-points');

fileUpload.addEventListener('change', () => {
  if (fileUpload.files.length > 0) {
    const fileName = fileUpload.files[0].name;
    uploadLabel.textContent = fileName;
    uploadLabel.classList.add('selected');
  } else {
    uploadLabel.textContent = 'Choose File';
    uploadLabel.classList.remove('selected');
  }
});

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData();
  formData.append('protocol', fileUpload.files[0]);

  uploadEvaluateBtn.textContent = 'Processing...';
  uploadEvaluateBtn.disabled = true;

  try {
    const response = await fetch('/upload-and-evaluate', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();

    if (result.error) {
      alert(`Error: ${result.error}`);
    } else {
      overallScore.textContent = result.score;
      executiveSummary.textContent = result.executive_summary;

      improvementPoints.innerHTML = '';
      result.improvement_points.forEach((point) => {
        const li = document.createElement('li');
        li.textContent = point;
        improvementPoints.appendChild(li);
      });
    }
  } catch (error) {
    alert('An error occurred while processing the document. Please try again.');
  } finally {
    uploadEvaluateBtn.textContent = 'Upload and Evaluate';
    uploadEvaluateBtn.disabled = false;
  }
});
