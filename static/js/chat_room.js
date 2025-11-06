
(function () {
  const form = document.querySelector('.chat-form');
  const messagesEl = document.getElementById('chat-messages');
  if (!form || !messagesEl) return;

  const textarea = form.querySelector('textarea[name="content"]');
  const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
  const csrftoken = csrfInput ? csrfInput.value : '';
  const userId = Number(form.dataset.userId || '0');
  const roomId = form.dataset.roomId;

  const socketScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socketUrl = `${socketScheme}://${window.location.host}/ws/chat/${roomId}/`;
  const chatSocket = new WebSocket(socketUrl);

  chatSocket.addEventListener('open', scrollToBottom);
  chatSocket.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type !== 'chat.message') return;
      appendMessage({
        message: data.message,
        sender: data.sender,
        senderId: Number(data.sender_id),
        timestamp: data.timestamp,
      });
    } catch (error) {
      console.error('Failed to parse websocket payload', error);
    }
  });
  chatSocket.addEventListener('close', () => console.warn('Chat socket closed.'));
  chatSocket.addEventListener('error', (err) => console.error('Chat socket error', err));

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const message = textarea.value.trim();
    if (!message) return;
    if (chatSocket.readyState !== WebSocket.OPEN) {
      alert('연결이 끊어졌습니다. 페이지를 새로고침 해주세요.');
      return;
    }
    chatSocket.send(JSON.stringify({ message }));
    textarea.value = '';
  });

  textarea.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  function appendMessage({ message, sender, senderId, timestamp }) {
    const isSelf = senderId === userId;
    const row = document.createElement('div');
    row.className = `message-row ${isSelf ? 'me' : 'other'}`;

    const bubble = document.createElement('div');
    bubble.className = `message ${isSelf ? 'me' : 'other'}`;

    const textEl = document.createElement('div');
    textEl.className = 'message__text';
    textEl.textContent = message;

    const timeEl = document.createElement('div');
    timeEl.className = 'timestamp';
    timeEl.textContent = timestamp;

    bubble.appendChild(textEl);
    bubble.appendChild(timeEl);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // ------------------------------------------------------------------
  // 주문/확정 로직 (기존 REST 기반 흐름 유지)
  // ------------------------------------------------------------------
  const actionsEl = document.querySelector('.chat-form__actions');
  if (!actionsEl) return;

  const purchaseBtn = document.querySelector('.chat-form__purchase');
  const confirmBtn = document.querySelector('.chat-form__confirm');
  const purchaseCodeEl = document.querySelector('.chat-purchase-code');

  const listingId = actionsEl.dataset.listingId || null;
  const buyerId = actionsEl.dataset.buyerId || null;
  const isSeller = actionsEl.dataset.isSeller === 'true';
  const isBuyer = actionsEl.dataset.isBuyer === 'true';

  let orderId = actionsEl.dataset.orderId || null;
  let hasOrder = actionsEl.dataset.hasOrder === 'true';
  let orderState = actionsEl.dataset.orderState || '';
  let orderConfirmed = actionsEl.dataset.orderConfirmed === 'true';
  let confirmationCode = actionsEl.dataset.initialCode || '';
  let buyerNotifiedForCode = orderConfirmed && !!confirmationCode;
  let sellerPollTimer = null;
  let buyerPollTimer = null;

  const codeTexts = purchaseCodeEl
    ? {
        empty: purchaseCodeEl.dataset.emptyText || '',
        pending: purchaseCodeEl.dataset.pendingText || '',
        completePrefix: purchaseCodeEl.dataset.completePrefix || '',
      }
    : null;

  function setOrderData(order) {
    if (!actionsEl) return;
    if (order && order.id) {
      orderId = String(order.id);
      hasOrder = true;
      orderState = order.escrow_state || '';
      orderConfirmed = orderState === 'RELEASED';
      if (order.confirmation_code) {
        confirmationCode = order.confirmation_code;
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
      buyerNotifiedForCode = false;
      actionsEl.dataset.orderId = '';
      actionsEl.dataset.hasOrder = 'false';
      actionsEl.dataset.orderConfirmed = 'false';
      actionsEl.dataset.orderState = '';
      actionsEl.dataset.initialCode = '';
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

  function applyOrderState(order) {
    const prevConfirmed = orderConfirmed;
    setOrderData(order);

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
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      const results = Array.isArray(data) ? data : Array.isArray(data.results) ? data.results : [];
      if (!results.length) return null;
      results.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      return results[0];
    } catch (error) {
      console.error('Failed to fetch order info', error);
      return null;
    }
  }

  function scheduleSellerPoll() {
    if (!isSeller || !confirmBtn) return;
    if (!hasOrder || orderConfirmed) {
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
    }, 5000);
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
    }, 5000);
  }

  if (purchaseBtn) {
    purchaseBtn.addEventListener('click', async () => {
      if (purchaseBtn.disabled) return;
      const listingAttr = purchaseBtn.dataset.listingId;
      const amountAttr = purchaseBtn.dataset.amount;
      if (!listingAttr || !amountAttr) return;

      const originalLabel = purchaseBtn.textContent.trim() || '구매하기';
      purchaseBtn.disabled = true;
      purchaseBtn.textContent = '구매 진행 중...';

      let createdOrder = null;

      try {
        const resp = await fetch('/api/orders/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
          },
          body: JSON.stringify({
            listing: Number(listingAttr),
            amount: Number(amountAttr),
          }),
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
          } catch (_) {
            /* ignore */
          }
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
    confirmBtn.addEventListener('click', async () => {
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
      confirmBtn.textContent = '확정 처리 중...';

      let confirmedOrder = null;

      try {
        const resp = await fetch(`/api/orders/${orderId}/confirm/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
          },
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
          } catch (_) {
            /* ignore */
          }
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

  const initialOrder = hasOrder
    ? {
        id: orderId,
        escrow_state: orderState || (orderConfirmed ? 'RELEASED' : 'HELD'),
        confirmation_code: confirmationCode,
      }
    : null;
  applyOrderState(initialOrder);
  updateCodeDisplay(false);
  scrollToBottom();
})();
