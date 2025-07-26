//! Complete S-expression parsing functions for KiCad parser

use nom::{
    IResult,
    branch::alt,
    bytes::complete::{tag, take_until, take_while1},
    character::complete::{char, multispace0, multispace1, digit1, alphanumeric1},
    combinator::{map, opt, recognize},
    multi::{many0, many1, separated_list0},
    sequence::{delimited, preceded, terminated, tuple},
};

use super::SExp;

/// Parse S-expression list
pub fn parse_list(input: &str) -> IResult<&str, SExp> {
    delimited(
        preceded(multispace0, char('(')),
        map(
            separated_list0(multispace1, parse_sexp),
            SExp::List
        ),
        preceded(multispace0, char(')'))
    )(input)
}

/// Parse S-expression atom
pub fn parse_atom(input: &str) -> IResult<&str, SExp> {
    preceded(
        multispace0,
        alt((
            parse_quoted_string,
            parse_unquoted_atom,
        ))
    )(input)
}

/// Parse quoted string
fn parse_quoted_string(input: &str) -> IResult<&str, SExp> {
    delimited(
        char('"'),
        map(
            take_until("\""),
            |s: &str| SExp::Atom(s.to_string())
        ),
        char('"')
    )(input)
}

/// Parse unquoted atom
fn parse_unquoted_atom(input: &str) -> IResult<&str, SExp> {
    map(
        take_while1(|c: char| !c.is_whitespace() && c != '(' && c != ')' && c != '"'),
        |s: &str| SExp::Atom(s.to_string())
    )(input)
}

/// Parse S-expression using nom
pub fn parse_sexp(input: &str) -> IResult<&str, SExp> {
    alt((parse_list, parse_atom))(input)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_atom() {
        let (_, result) = parse_atom("hello").unwrap();
        match result {
            SExp::Atom(s) => assert_eq!(s, "hello"),
            _ => panic!("Expected atom"),
        }
    }

    #[test]
    fn test_parse_quoted_string() {
        let (_, result) = parse_atom("\"hello world\"").unwrap();
        match result {
            SExp::Atom(s) => assert_eq!(s, "hello world"),
            _ => panic!("Expected atom"),
        }
    }

    #[test]
    fn test_parse_list() {
        let (_, result) = parse_sexp("(hello world)").unwrap();
        match result {
            SExp::List(items) => {
                assert_eq!(items.len(), 2);
                match (&items[0], &items[1]) {
                    (SExp::Atom(a), SExp::Atom(b)) => {
                        assert_eq!(a, "hello");
                        assert_eq!(b, "world");
                    }
                    _ => panic!("Expected atoms"),
                }
            }
            _ => panic!("Expected list"),
        }
    }

    #[test]
    fn test_parse_nested_list() {
        let (_, result) = parse_sexp("(outer (inner value))").unwrap();
        match result {
            SExp::List(items) => {
                assert_eq!(items.len(), 2);
                match &items[1] {
                    SExp::List(inner) => assert_eq!(inner.len(), 2),
                    _ => panic!("Expected nested list"),
                }
            }
            _ => panic!("Expected list"),
        }
    }
}