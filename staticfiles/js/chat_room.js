(function () {
  const form = document.querySelector(".chat-form");
  const messagesEl = document.getElementById("chat-messages");
  if (!form || !messagesEl) return;

  const textarea = form.querySelector('textarea[name="content"]');
  if (!textarea) return;

  const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
  const csrftoken = csrfInput ? csrfInput.value : "";
  const submitButton = form.querySelector(".chat-form__send");
  const purchaseBtn = form.querySelector(".chat-form__purchase");

  textarea.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else if (submitButton) {
        submitButton.click();
      }
    }
  });

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function makeMessageNode(data) {
    const row = document.createElement("div");
    row.className = "message-row me";
    const msg = document.createElement("div");
    msg.className = "message me";
    msg.innerHTML = `${data.content}<div class="timestamp">${data.timestamp}</div>`;
    row.appendChild(msg);
    return row;
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const content = textarea.value.trim();
    if (!content) return;

    try {
      const resp = await fetch(window.location.href, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        body: new URLSearchParams({ content }),
      });

      if (resp.ok) {
        const data = await resp.json();
        const node = makeMessageNode(data);
        messagesEl.appendChild(node);
        textarea.value = "";
        scrollToBottom();
      } else {
        form.removeEventListener("submit", arguments.callee);
        form.submit();
      }
    } catch (err) {
      console.error(err);
      form.removeEventListener("submit", arguments.callee);
      form.submit();
    }
  });

  if (purchaseBtn) {
    purchaseBtn.addEventListener("click", async function () {
      const listingId = purchaseBtn.dataset.listingId;
      const amount = purchaseBtn.dataset.amount;
      if (!listingId || !amount) return;

      const originalLabel = purchaseBtn.textContent.trim() || "구매하기";
      purchaseBtn.disabled = true;
      purchaseBtn.textContent = "구매 진행중...";

      try {
        const resp = await fetch("/api/orders/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({
            listing: Number(listingId),
            amount: Number(amount),
          }),
        });

        if (resp.ok) {
          alert("구매 요청이 접수되었습니다.");
        } else {
          let message = "구매 요청 처리 중 오류가 발생했습니다.";
          try {
            const data = await resp.json();
            if (data) {
              if (typeof data.detail === "string") {
                message = data.detail;
              } else {
                const firstValue = Object.values(data)[0];
                if (Array.isArray(firstValue) && firstValue.length) {
                  message = firstValue[0];
                }
              }
            }
          } catch (_) {}
          alert(message);
        }
      } catch (error) {
        console.error(error);
        alert("구매 요청 처리 중 오류가 발생했습니다.");
      } finally {
        purchaseBtn.disabled = false;
        purchaseBtn.textContent = originalLabel;
      }
    });
  }

  scrollToBottom();
})();

