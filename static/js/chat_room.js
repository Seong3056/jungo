(function () {
  const form = document.querySelector('.chat-form');
  const messagesEl = document.getElementById('chat-messages');
  if (!form || !messagesEl) return;

  const textarea = form.querySelector('textarea[name="content"]');
  if (!textarea) return;

  const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
  const csrftoken = csrfInput ? csrfInput.value : '';

  const submitButton = form.querySelector('.chat-form__send');
  const purchaseBtn = form.querySelector('.chat-form__purchase');
  const confirmBtn = form.querySelector('.chat-form__confirm');
  const actionsEl = form.querySelector('.chat-form__actions');
  const purchaseCodeEl = document.querySelector('.chat-purchase-code');
  const POLL_INTERVAL = 5000;

  const listingId = actionsEl ? actionsEl.dataset.listingId : null;
  const buyerId = actionsEl ? actionsEl.dataset.buyerId : null;
  const isSeller = actionsEl ? actionsEl.dataset.isSeller === 'true' : false;
  const isBuyer = actionsEl ? actionsEl.dataset.isBuyer === 'true' : false;

  let orderId = actionsEl && actionsEl.dataset.orderId ? actionsEl.dataset.orderId : null;
  let hasOrder = actionsEl ? actionsEl.dataset.hasOrder === 'true' : false;
  let orderState = actionsEl ? actionsEl.dataset.orderState || '' : '';
  let orderConfirmed = actionsEl ? actionsEl.dataset.orderConfirmed === 'true' : false;
  let confirmationCode = actionsEl ? actionsEl.dataset.initialCode || '' : '';

  let sellerPollTimer = null;
  let buyerPollTimer = null;
  let buyerNotifiedForCode = orderConfirmed && !!confirmationCode;

  const codeTexts = purchaseCodeEl
    ? {
        empty: purchaseCodeEl.dataset.emptyText || '',
        pending: purchaseCodeEl.dataset.pendingText || '',
        completePrefix: purchaseCodeEl.dataset.completePrefix || ''
      }
    : null;

  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (typeof form.requestSubmit === 'function') {
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
    const row = document.createElement('div');
    row.className = 'message-row me';
    const msg = document.createElement('div');
    msg.className = 'message me';
    msg.innerHTML = `${data.content}<div class="timestamp">${data.timestamp}</div>`;
    row.appendChild(msg);
    return row;
  }

  function setOrderState(orderData) {
    if (!actionsEl) return;
    if (orderData && orderData.id) {
      orderId = String(orderData.id);
      hasOrder = true;
      orderState = orderData.escrow_state || '';
      orderConfirmed = orderState === 'RELEASED';
      if (typeof orderData.confirmation_code === 'string' && orderData.confirmation_code.length) {
        confirmationCode = orderData.confirmation_code;
      }
      actionsEl.dataset.orderId = orderId;
      actionsEl.dataset.hasOrder = 'true';
      actionsEl.dataset.orderConfirmed = orderConfirmed ? 'true' : 'false';
      actionsEl.dataset.orderState = orderState;
      actionsEl.dataset.initialCode = confirmationCode || '';
    } else {
      orderId = null;
      hasOrder = false;
      orderState = '';
      orderConfirmed = false;
      confirmationCode = '';
      actionsEl.dataset.orderId = '';
      actionsEl.dataset.hasOrder = 'false';
      actionsEl.dataset.orderConfirmed = 'false';
      actionsEl.dataset.orderState = '';
      actionsEl.dataset.initialCode = '';
      buyerNotifiedForCode = false;
    }
  }

  function updateCodeDisplay(triggerAlert) {
    if (!purchaseCodeEl || !isBuyer || !codeTexts) return;
    if (!hasOrder) {
      purchaseCodeEl.textContent = codeTexts.empty;
      return;
    }
    if (orderConfirmed && confirmationCode) {
      purchaseCodeEl.innerHTML = `${codeTexts.completePrefix}<span class="chat-purchase-code__value">${confirmationCode}</span>`;
      if (triggerAlert && !buyerNotifiedForCode) {
        alert(`${codeTexts.completePrefix}${confirmationCode}`);
        buyerNotifiedForCode = true;
      }
    } else {
      purchaseCodeEl.textContent = codeTexts.pending || codeTexts.empty;
    }
  }

  function applyOrderState(orderData) {
    const prevConfirmed = orderConfirmed;
    setOrderState(orderData);

    if (purchaseBtn) {
      if (!hasOrder) {
        purchaseBtn.disabled = false;
        purchaseBtn.textContent = '구매하기';
      } else {
        purchaseBtn.disabled = true;
        purchaseBtn.textContent = orderConfirmed ? '구매완료' : '구매요청됨';
      }
    }

    if (confirmBtn) {
      if (!hasOrder) {
        confirmBtn.disabled = true;
        confirmBtn.textContent = '구매확정';
      } else if (orderConfirmed) {
        confirmBtn.disabled = true;
        confirmBtn.textContent = '구매확정 완료';
      } else {
        confirmBtn.disabled = false;
        confirmBtn.textContent = '구매확정';
      }
    }

    if (!orderConfirmed) {
      buyerNotifiedForCode = false;
    }

    const becameConfirmed = !prevConfirmed && orderConfirmed;
    updateCodeDisplay(becameConfirmed && isBuyer);

    if (orderConfirmed && sellerPollTimer) {
      clearTimeout(sellerPollTimer);
      sellerPollTimer = null;
    }
    if (orderConfirmed && buyerPollTimer) {
      clearTimeout(buyerPollTimer);
      buyerPollTimer = null;
    }

    scheduleSellerPoll();
    scheduleBuyerPoll();
  }

  async function fetchLatestOrder() {
    if (!listingId || !buyerId) return null;
    try {
      const params = new URLSearchParams({ listing: listingId, buyer: buyerId });
      const resp = await fetch(`/api/orders/?${params.toString()}`, {
        headers: { Accept: 'application/json' }
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      let orders = [];
      if (Array.isArray(data)) {
        orders = data;
      } else if (data && Array.isArray(data.results)) {
        orders = data.results;
      }
      if (orders.length) {
        orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        return orders[0];
      }
    } catch (error) {
      console.error(error);
    }
    return null;
  }

  function scheduleSellerPoll() {
    if (!isSeller || !confirmBtn) return;
    if (orderConfirmed) {
      if (sellerPollTimer) {
        clearTimeout(sellerPollTimer);
        sellerPollTimer = null;
      }
      return;
    }
    if (sellerPollTimer) return;
    sellerPollTimer = setTimeout(async () => {
      sellerPollTimer = null;
      const latest = await fetchLatestOrder();
      if (latest) {
        applyOrderState(latest);
      } else {
        scheduleSellerPoll();
      }
    }, POLL_INTERVAL);
  }

  function scheduleBuyerPoll() {
    if (!isBuyer || !purchaseBtn) return;
    if (!hasOrder || orderConfirmed) {
      if (buyerPollTimer) {
        clearTimeout(buyerPollTimer);
        buyerPollTimer = null;
      }
      return;
    }
    if (buyerPollTimer) return;
    buyerPollTimer = setTimeout(async () => {
      buyerPollTimer = null;
      const latest = await fetchLatestOrder();
      if (latest) {
        applyOrderState(latest);
      } else {
        scheduleBuyerPoll();
      }
    }, POLL_INTERVAL);
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const content = textarea.value.trim();
    if (!content) return;

    try {
      const resp = await fetch(window.location.href, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrftoken,
          Accept: 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        },
        body: new URLSearchParams({ content })
      });

      if (resp.ok) {
        const data = await resp.json();
        const node = makeMessageNode(data);
        messagesEl.appendChild(node);
        textarea.value = '';
        scrollToBottom();
      } else {
        form.removeEventListener('submit', arguments.callee);
        form.submit();
      }
    } catch (err) {
      console.error(err);
      form.removeEventListener('submit', arguments.callee);
      form.submit();
    }
  });

  if (purchaseBtn) {
    purchaseBtn.addEventListener('click', async function () {
      if (purchaseBtn.disabled) return;
      const listingIdAttr = purchaseBtn.dataset.listingId;
      const amountAttr = purchaseBtn.dataset.amount;
      if (!listingIdAttr || !amountAttr) return;

      const originalLabel = purchaseBtn.textContent.trim() || '구매하기';
      purchaseBtn.disabled = true;
      purchaseBtn.textContent = '구매 진행중...';

      let createdOrder = null;

      try {
        const resp = await fetch('/api/orders/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken
          },
          body: JSON.stringify({
            listing: Number(listingIdAttr),
            amount: Number(amountAttr)
          })
        });

        if (resp.ok) {
          createdOrder = await resp.json();
          applyOrderState(createdOrder);
          alert('구매 요청이 접수되었습니다.');
        } else {
          let message = '구매 요청 처리 중 오류가 발생했습니다.';
          try {
            const data = await resp.json();
            if (data) {
              if (typeof data.detail === 'string') {
                message = data.detail;
              } else {
                const firstValue = Object.values(data)[0];
                if (Array.isArray(firstValue) && firstValue.length) {
                  message = firstValue[0];
                }
              }
            }
          } catch (_) { }
          alert(message);
        }
      } catch (error) {
        console.error(error);
        alert('구매 요청 처리 중 오류가 발생했습니다.');
      } finally {
        if (!createdOrder) {
          purchaseBtn.disabled = false;
          purchaseBtn.textContent = originalLabel;
        }
      }
    });
  }

  if (confirmBtn) {
    confirmBtn.addEventListener('click', async function () {
      if (confirmBtn.disabled) return;

      if (!orderId) {
        const latest = await fetchLatestOrder();
        if (!latest) {
          alert('대기 중인 주문이 없습니다.');
          return;
        }
        applyOrderState(latest);
      }

      if (!orderId) {
        alert('대기 중인 주문이 없습니다.');
        return;
      }

      const originalLabel = confirmBtn.textContent.trim() || '구매확정';
      confirmBtn.disabled = true;
      confirmBtn.textContent = '확정 처리중...';

      let confirmedOrder = null;

      try {
        const resp = await fetch(`/api/orders/${orderId}/confirm/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken
          }
        });

        if (resp.ok) {
          confirmedOrder = await resp.json();
          applyOrderState(confirmedOrder);
          alert('구매가 확정되었습니다.');
        } else {
          let message = '구매확정 처리 중 오류가 발생했습니다.';
          try {
            const data = await resp.json();
            if (data && typeof data.detail === 'string') {
              message = data.detail;
            }
          } catch (_) { }
          alert(message);
        }
      } catch (error) {
        console.error(error);
        alert('구매확정 처리 중 오류가 발생했습니다.');
      } finally {
        if (!confirmedOrder) {
          confirmBtn.disabled = false;
          confirmBtn.textContent = originalLabel;
        }
      }
    });
  }

  const initialData = hasOrder
    ? {
        id: orderId,
        escrow_state: orderState || (orderConfirmed ? 'RELEASED' : 'HELD'),
        confirmation_code: confirmationCode
      }
    : null;
  applyOrderState(initialData);

  scrollToBottom();
})();
