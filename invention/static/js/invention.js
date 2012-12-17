$(function() {
  $('.navbar-search .search-query').typeahead({
    minLength: 3,
    source: function(query, process) {
      $.getJSON('/_autocomplete/', {query: query}, function(data) {
        process(data.results);
      });
    },
    updater: function(item) {
      this.$element.val(item);
      this.$element.parent('form').submit();
    }
  });
});
