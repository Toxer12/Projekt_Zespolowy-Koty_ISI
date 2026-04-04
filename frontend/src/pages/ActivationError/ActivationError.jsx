function ActivationError() {
  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>Activation Failed</h1>
      <p>The link is invalid or has expired.</p>
      <a href="/register">Register again</a>
    </div>
  );
}
export default ActivationError;