$(function() {
    $('.delete-file-form').submit(e => {
        e.preventDefault();
        if (confirm('Confirm delete for this file')) e.target.submit();
    });
    })