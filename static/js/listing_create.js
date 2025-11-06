document.addEventListener("DOMContentLoaded", () => {
  const input = document.querySelector('input[type="file"][name="image"]');
  const preview = document.getElementById("preview-container");
  if (!input || !preview) return;

  input.addEventListener("change", (event) => {
    preview.innerHTML = "";
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("이미지 파일만 업로드할 수 있습니다.");
      input.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const img = new Image();
      img.src = ev.target.result;
      img.style.width = "140px";
      img.style.height = "140px";
      img.style.objectFit = "cover";
      img.style.borderRadius = "12px";
      img.style.border = "1px solid rgba(255,255,255,0.3)";
      preview.appendChild(img);
    };
    reader.readAsDataURL(file);
  });
});

