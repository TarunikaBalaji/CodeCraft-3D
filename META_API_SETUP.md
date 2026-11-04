# Meta Model API setup for CODECRAFT 3D

1. Open the official Meta Model API dashboard: https://dev.meta.ai/
2. Sign in, open **API keys**, choose **Create API key**, and copy it immediately. Meta says the key is only shown once.
3. In the CODECRAFT 3D project root, copy `.env.example` to `.env`.
4. Set `MODEL_API_KEY` in `.env` to the key. Do not commit or upload `.env`.
5. Restart Streamlit. The Regulation Intelligence Engine should enable the Analyse button.

This project calls `POST https://api.meta.ai/v1/responses` with model `muse-spark-1.3`, using Bearer authentication. The request is made only when you click **Analyse with Muse Spark**.

Official docs:
- Overview: https://dev.meta.ai/docs/overview
- Authentication: https://dev.meta.ai/docs/authentication
- Quickstart: https://dev.meta.ai/docs/quickstart

Billing note: Model API is pay-as-you-go. Check the current pricing and rate limits in the official dashboard before making the first live call. The app does not impose a provider-side spending cap; do not assume a local UI limit can prevent billing.
