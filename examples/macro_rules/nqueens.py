# coding: macro_polo
"""A compile-time implementation of a solution to the N-Queens problem.

The nqueens macro takes n `Q` tokens (unquoted), and produces a string representing an
n x n chess board, with n queens placed such that no queen is threatening another.

To see power of compile-time execution, run this file as a module and compare run time
before and after Python caches the bytecode. (Alternatively, you can  compile the script
manually with `python3 -m compileall examples/nqueens.py`.)
"""

macro_rules! nqueens:
    # Entry point
    [Q $(Q $qs_tail:null)*]:
        nqueens!(
            @solve
            qs: [Q $(Q $qs_tail)*]
            remaining_qs: [$(Q $qs_tail)*]
            rows: []
            rows_to_check: []
            curr_row: [Q $(Q $qs_tail)*]
            shift: [Q]
            checks:
                left: [] []
                down: [] []
                right: [] []
        )

    # Solved
    [
        @solve
        qs: $qs:tt
        remaining_qs: []
        rows: [$($rows:tt)*]
        rows_to_check: []
        curr_row: $curr_row:tt
        shift: $_:tt
        checks:
            left: [] []
            down: [] []
            right: [] []
    ]:
        nqueens!(
            @format_board
            qs: $qs
            board: [$curr_row $($rows)*]
        )

    # Row passed all checks, add another row
    [
        @solve
        qs: [$($qs:tt)*]
        remaining_qs: [Q $($remaining_qs_tail:tt)*]
        rows: [$($rows:tt)*]
        rows_to_check: []
        curr_row: [$($curr_row:tt)*]
        shift: $_:tt
        checks:
            left: [] []
            down: [] []
            right: [] []
    ]:
        nqueens!(
            @solve
            qs: [$($qs)*]
            remaining_qs: [$($remaining_qs_tail)*]
            rows: [[$($curr_row)*] $($rows)*]
            rows_to_check: [$($rows)*]
            curr_row: [$($qs)*]
            shift: [Q]
            checks:
                left:
                    [$($qs)*]
                    [Q $($curr_row)*]
                down:
                    [$($qs)*]
                    [$($curr_row)*]
                right:
                    [Q $($qs)*]
                    [$($curr_row)*]
        )

    # Row passed single check, check against next row
    [
        @solve
        qs: $qs:tt
        remaining_qs: $remaining_qs:tt
        rows: [$($rows:tt)*]
        rows_to_check: [
            [$($next_row_to_check:tt)*]
            $($rows_to_check_tail:tt)*
        ]
        curr_row: [$($curr_row:tt)*]
        shift: [$($shift:tt)*]
        checks:
            left: [] []
            down: [] []
            right: [] []
    ]:
        nqueens!(
            @solve
            qs: $qs
            remaining_qs: $remaining_qs
            rows: [$($rows)*]
            rows_to_check: [$($rows_to_check_tail)*]
            curr_row: [$($curr_row)*]
            shift: [Q $($shift)*]
            checks:
                left:
                    [$($curr_row)*]
                    [Q $($shift)* $($next_row_to_check)*]
                down:
                    [$($curr_row)*]
                    [$($next_row_to_check)*]
                right:
                    [Q $($shift)* $($curr_row)*]
                    [$($next_row_to_check)*]
        )

    # Threat detected, no solution
    [
        @solve
        qs: $qs:tt
        remaining_qs: $remaining_qs:tt
        rows: [[Q]]
        rows_to_check: $_:tt
        curr_row: [Q]
        shift: $_:tt
        checks: $[(
            left: [Q] [Q]
            down: $_:tt $_:tt
            right: $_:tt $_:tt
        )|(
            left: $_:tt $_:tt
            down: [Q] [Q]
            right: $_:tt $_:tt
        )|(
            left: $_:tt $_:tt
            down: $_:tt $_:tt
            right: [Q] [Q]
        )]
    ]:
        'No solutions!'

    # Threat detected, backtrack
    [
        @solve
        qs: $qs:tt
        remaining_qs: [$($remaining_qs:tt)*]
        rows: [
            $([Q] $backtracked_rows:null)*
            [Q $($new_curr_row:tt)*]
            $([$($new_row_to_check:tt)*])?
            $($rows_tail:tt)*
        ]
        rows_to_check: $_:tt
        curr_row: [Q]
        shift: $_:tt
        checks: $[(
            left: [Q] [Q]
            down: $_:tt $_:tt
            right: $_:tt $_:tt
        )|(
            left: $_:tt $_:tt
            down: [Q] [Q]
            right: $_:tt $_:tt
        )|(
            left: $_:tt $_:tt
            down: $_:tt $_:tt
            right: [Q] [Q]
        )]
    ]:
        nqueens!(
            @solve
            qs: $qs
            remaining_qs: [Q $(Q $backtracked_rows)* $($remaining_qs)*]
            rows: [
                $([$($new_row_to_check)*])*
                $($rows_tail)*
            ]
            rows_to_check: [$($rows_tail)*]
            curr_row: [$($new_curr_row)*]
            shift: [Q]
            checks:
                left:
                    [$($new_curr_row)*]
                    [$(Q $($new_row_to_check)*)*]
                down:
                    [$($new_curr_row)*]
                    [$($($new_row_to_check)*)*]
                right:
                    [Q $($new_curr_row)*]
                    [$($($new_row_to_check)*)*]
        )

    # Threat detected, try next space in current row
    [
        @solve
        qs: $qs:tt
        remaining_qs: $remaining_qs:tt
        rows: [
            [$($prev_row:tt)*]
            $($rows_tail:tt)*
        ]
        rows_to_check: $_:tt
        curr_row: [Q $($new_curr_row:tt)*]
        shift: $_:tt
        checks: $[(
            left: [Q] [Q]
            down: $_:tt $_:tt
            right: $_:tt $_:tt
        )|(
            left: $_:tt $_:tt
            down: [Q] [Q]
            right: $_:tt $_:tt
        )|(
            left: $_:tt $_:tt
            down: $_:tt $_:tt
            right: [Q] [Q]
        )]
    ]:
        nqueens!(
            @solve
            qs: $qs
            remaining_qs: $remaining_qs
            rows: [
                [$($prev_row)*]
                $($rows_tail)*
            ]
            rows_to_check: [$($rows_tail)*]
            curr_row: [$($new_curr_row)*]
            shift: [Q]
            checks:
                left:
                    [$($new_curr_row)*]
                    [Q $($prev_row)*]
                down:
                    [$($new_curr_row)*]
                    [$($prev_row)*]
                right:
                    [Q $($new_curr_row)*]
                    [$($prev_row)*]
        )

    # Keep checking row
    [
        @solve
        qs: $qs:tt
        remaining_qs: $remaining_qs:tt
        rows: $rows:tt
        rows_to_check: $rows_to_check:tt
        curr_row: $curr_row:tt
        shift: $shift:tt
        checks:
            left:
                [$(Q)? $($left_curr:tt)*]
                [$(Q)? $($left_prev:tt)*]
            down:
                [$(Q)? $($down_curr:tt)*]
                [$(Q)? $($down_prev:tt)*]
            right:
                [$(Q)? $($right_curr:tt)*]
                [$(Q)? $($right_prev:tt)*]
    ]:
        nqueens!(
            @solve
            qs: $qs
            remaining_qs: $remaining_qs
            rows: $rows
            rows_to_check: $rows_to_check
            curr_row: $curr_row
            shift: $shift
            checks:
                left:
                    [$($left_curr)*]
                    [$($left_prev)*]
                down:
                    [$($down_curr)*]
                    [$($down_prev)*]
                right:
                    [$($right_curr)*]
                    [$($right_prev)*]
        )

    # Format solution
    [
        @format_board
        qs: $qs:tt
        board: [$first_row:tt $($rows_tail:tt)*]
    ]:
        (
            nqueens!(@format_top_border qs: $qs)
            nqueens!(@format_row qs: $qs row: $first_row)
            $(
                nqueens!(@format_inner_border qs: $qs)
                nqueens!(@format_row qs: $qs row: $rows_tail)
            )*
            nqueens!(@format_bottom_border qs: $qs)
        )

    [@format_top_border qs: [$(Q $qs_counter:null)*]]:
        '╭' $('───' $qs_counter)'┰'* '╮\n'

    [@format_inner_border qs: [$(Q $qs_counter:null)*]]:
        '┝' $('━━━' $qs_counter)'╋'* '┥\n'

    [@format_bottom_border qs: [$(Q $qs_counter:null)*]]:
        '╰' $('───' $qs_counter)'┸'* '╯'

    [
        @format_row
        qs: [$(Q $qs_counter:null)*]
        row: [Q $(Q $offset_counter:null)*]
    ]:
        '│' $('   ┃' $offset_counter)* ' Q ' \
        nqueens!(@format_row_end
            qs: [$(Q $qs_counter)*]
            row: [Q $(Q $offset_counter)*]
        ) \
        '│\n'

    [
        @format_row_end
        qs: [Q $($qs:tt)*]
        row: [Q $($row:tt)*]
    ]:
        nqueens!(
            @format_row_end
            qs: [$($qs)*]
            row: [$($row)*]
        )

    [
        @format_row_end
        qs: [$(Q $space:null)*]
        row: []
    ]:
        $('┃   ' $space)*

print(nqueens!(Q Q Q Q Q Q))
