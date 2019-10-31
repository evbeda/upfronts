$( function() {
  $( "#datepicker_signed_date" ).datepicker();
  $( "#datepicker_max_payment_date" ).datepicker();
  $( "#datepicker_payment_date" ).datepicker();
} );

const csvExportLink = document.querySelector("#export-csv");
if (csvExportLink) {
  const currentUrl = window.location.href;
  const connector = currentUrl.includes("?") ? "&" : "?";
  const uriParam = connector + "download=true";
  csvExportLink.href = currentUrl + uriParam;
}
