// #region hardcoded_sql_expressions_merge_function 

var dangerous_merge_function_direct = concat('SELECT Id FROM ', a, b);

var dangerous_merge_function_caller_string = 'SELECT Id FROM '.concat(a, b);

var dangerous_merge_function_caller_member_expression = x.y.z.concat('SELECT Id FROM ', b);

var dangerous_merge_function_mixed_arguments = a.concat('SELECT Id FROM ', b); 

var dangerous_merge_function_join = ['SELECT Id FROM ', query].join('');

var dangerous_merge_function_spread_concat = "SELECT Id FROM ".concat(...queryList);

// #endregion

// #region hardcoded_sql_expressions_with_plus 

var dangerous_with_plus_mixed_identifier_literal = 'SELECT Id FROM ' + query + 'WHERE Id = 6';

var dangerous_with_plus_mixed_expression_literal = 'SELECT Id FROM ' + query['key'];

var dangerous_with_plus_mixed_complex_literal = '' + ('SELECT Id FROM ' + query)

var dangerous_with_plus_a_string_and_a_number = "SELECT Id FROM MyTable WHERE Id = " + 2

var safe_with_plus_mixed_expression_literal_escape = "SELECT * FROM MyTable WHERE Id = " + connection.escape(id);

var safe_with_plus_two_literal = 'SELECT Id FROM MyTable' + ' WHERE Id = 5'

// #endregion

// #region hardcoded_sql_expressions_with_template_literal 

var dangerous_with_template_literal_function  = `SELECT Id FROM MyTable WHERE Id = ${expression()}`; 

var dangerous_with_template_literal_expression  = `SELECT Id FROM MyTable WHERE Id = ${a() + 2 + 4}`; 

// #endregion

// #region hardcoded_sql_expressions_with_plus_equal 

var dangerous_with_plus_equal_identifier  = ''
dangerous_with_plus_equal_identifier += 'SELECT Id FROM '
dangerous_with_plus_equal_identifier += 'MyTable WHERE Id = '
dangerous_with_plus_equal_identifier += '232'

// #endregion









